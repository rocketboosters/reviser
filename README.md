# Reviser (v0.2.2)

[![PyPI version](https://badge.fury.io/py/reviser.svg)](https://pypi.org/project/reviser/)
[![build status](https://gitlab.com/rocket-boosters/reviser/badges/main/pipeline.svg)](https://gitlab.com/rocket-boosters/reviser/commits/main)
[![coverage report](https://gitlab.com/rocket-boosters/reviser/badges/main/coverage.svg)](https://gitlab.com/rocket-boosters/reviser/commits/main)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Code style: flake8](https://img.shields.io/badge/code%20style-flake8-white)](https://gitlab.com/pycqa/flake8)
[![Code style: mypy](https://img.shields.io/badge/code%20style-mypy-white)](http://mypy-lang.org/)
[![PyPI - License](https://img.shields.io/pypi/l/reviser)](https://pypi.org/project/reviser/)

Reviser is a tool for AWS Lambda function and layer version deployment and
alias management specifically for Python runtimes where the actual
infrastructure is managed separately, mostly likely by CloudFormation or
Terraform. There are a number of ways to manage AWS Lambda functions and layers
already, but their generality and all-encompassing approaches don't integrate
well with certain workflows and can be overly complex for many needs.

Reviser is scoped to facilitate the deployment and updating of AWS Lambda
Python functions and layers for all of the version-specific configurations,
e.g. code bundles, environment variables, memory size, and timeout lengths.
The expectation is that functions are created by other means and then
configuration for versions is managed with the reviser through an interactive
or scripted shell of commands.

- [Basic Usage](#basic-usage)
- [Shell Commands](#shell-commands)
   - [alias](#alias)
   - [bundle](#bundle)
   - [configs](#configs)
   - [deploy](#deploy)
   - [exit](#exit)
   - [help (?)](#help-)
   - [list](#list)
   - [prune](#prune)
   - [push](#push)
   - [region](#region)
   - [reload](#reload)
   - [select](#select)
   - [shell](#shell)
   - [status](#status)
- [Configuration Files](#configuration-files)
   - [bucket(s)](#buckets)
   - [AWS region](#aws-region)
   - [targets](#targets)
      - [targets[N].kind](#targetsnkind)
      - [targets[N].name(s)](#targetsnnames)
      - [targets[N].region](#targetsnregion)
      - [targets[N].dependencies](#targetsndependencies)
      - [targets[N].dependencies(kind="pipper")](#targetsndependencieskindpipper)
      - [targets[N].dependencies(kind="poetry")](#targetsndependencieskindpoetry)
      - [targets[N].bundle](#targetsnbundle)
         - [targets[N].bundle.include(s)](#targetsnbundleincludes)
         - [targets[N].bundle.exclude(s)](#targetsnbundleexcludes)
         - [targets[N].bundle.omit_package(s)](#targetsnbundleomit_packages)
         - [targets[N].bundle.handler](#targetsnbundlehandler)
   - [function targets](#function-targets)
      - [(function) targets[N].layer(s)](#function-targetsnlayers)
      - [(function) targets[N].memory](#function-targetsnmemory)
      - [(function) targets[N].timeout](#function-targetsntimeout)
      - [(function) targets[N].variable(s)](#function-targetsnvariables)
      - [(function) targets[N].ignore(s)](#function-targetsnignores)
   - [run](#run)
- [Local Execution](#local-execution)

# Basic Usage

A project defines one or more lambda function configuration targets in a 
`lambda.yaml` file in the root project directory. The most basic configuration
looks like this:

```yaml
bucket: name-of-s3-bucket-for-code-uploads
targets:
- kind: function
  name: foo-function
```

This configuration defines a single `foo-function` lambda function target that
will be managed by reviser. The expectation is that this function exists and
was created by another means, e.g. CloudFormation or Terraform. A bucket must
be specified to indicate where the zipped code bundles will be uploaded prior
to them being applied to the target(s). The bucket must already exist as well.

By default the package will include no external, e.g. pip, package
dependencies. It will search for the first folder in the directory where the
`lambda.yaml` file is located that contains an `__init__.py` file, identifying
that folder as a Python source package for the function. It will also look for
a `lambda_function.py` alongside the `lambda.yaml` file to serve as the 
entrypoint. These will be included in the uploaded and deployed code bundle
when a `push` or a `deploy` command is executed. These default settings can
all be configured along with many more as will be outlined below.

To deploy this example project, install the reviser python library and
start the shell with the command `reviser` in your terminal of choice
in the directory where the `lambda.yaml` file resides. Docker must be running
and available in the terminal in which you execute this command, as reviser
is a containerized shell environment that runs within a container that mimics
the actual AWS Lambda runtime environment. Then run the `push` command within
the launched shell to create and upload the bundled source code and publish
a new version of the `foo-function` lambda function with the uploaded results.

# Shell commands

The reviser command starts an interactive shell within a Docker container 
compatible with the AWS Python Lambda runtime. This shell contains various
commands for deploying and managing deployments of lambda functions and layers
defined in a project's `lambda.yaml` configuration file, the format of which
is described later in this document. The shell commands are:

## alias

Assigns an alias to the specified version of the selected or specified lambda
function. Or it will create a new alias and assign it to the specified version
if the --create flag is included.

```
usage: alias [--function FUNCTION] [--yes] [--create] alias version

positional arguments:
  alias                Name of an existing alias to move to the specified
                       version, or the name of an alias to create and assign
                       to the specified function version if the --create flag
                       is included to allow for creating a new alias.
  version              Version of the function that the alias should be
                       assigned to. This will either be an integer value or
                       $LATEST. To see what versions are available for a given
                       function use the list command.

optional arguments:
  --function FUNCTION  The alias command only acts on one function. This can
                       be achieved either by selecting the function target via
                       the select command, or specifying the function name to
                       apply this change to with this flag.
  --yes                By default this command will require input confirmation
                       before carrying out the change. Specify this flag to
                       skip input confirmation and proceed without a breaking
                       prompt.
  --create             When specified the alias will be created instead of
                       reassigned. Use this to create and assign new aliases
                       to a function. When this flag is not specified, the
                       command will fail if the alias doesn't exist, which
                       helps prevent accidental alias creation.

```

To assign an existing `test` alias to version 42 of the selected
function, the command would be:

```
> alias test 42
```

If multiple functions are currently selected, use `--function=<NAME>`
to identify the function to which the alias change will be applied.

## bundle

Installs dependencies and copies includes into a zipped file that is structured
correctly to be deployed to the lambda function/layer target.

```
usage: bundle [--reinstall]

optional arguments:
  --reinstall  Add this flag to reinstall dependencies on a repeated bundle
               operation. By default, dependencies will remain cached for the
               lifetime of the shell to speed up the bundling process. This
               will force dependencies to be installed even if they had been
               installed previously.

```

## configs

Displays the configs loaded from the lambda.yaml file and fully populated with
defaults and dynamic values. Use this to inspect and validate that the loaded
configuration meets expectations when parsed into the reviser shell.

```
usage: configs

```

## deploy

Uploads the bundled contents to the upload S3 bucket and then publishes a new
version of each of the lambda targets with that new bundle and any modified
settings between the current configuration and that target's existing
configuration. This command will fail if a target being deployed has not
already been bundled.

```
usage: deploy [--description DESCRIPTION] [--dry-run]

optional arguments:
  --description DESCRIPTION
                        Specify a message to assign to the version published
                        by the deploy command.
  --dry-run             If set, the deploy operation will be exercised without
                        actually carrying out the actions. This can be useful
                        to validate the deploy process without side effects.

```

## exit

Exits the shell and returns to the parent terminal.

```
usage: exit

```

## help (?)

Displays help information on the commands available within the shell.
Additional help on each command can be found using the --help flag on the
command in question.

```
usage: help

```

## list

Lists versions of the specified lambda targets with info about each version.

```
usage: list

```

## prune

Removes old function and/or layer versions for the selected targets.

```
usage: prune [--start START] [--end END] [--dry-run] [-y]

optional arguments:
  --start START  Keep versions lower (earlier/before) this one.
  --end END      Do not prune versions higher than this value.
  --dry-run      Echo pruning operation without actually executing it.
  -y, --yes      Run the prune process without reviewing first.

```

## push

Combined single command for bundling and deploying the selected targets.

```
usage: push [--reinstall] [--description DESCRIPTION] [--dry-run]

optional arguments:
  --reinstall           Add this flag to reinstall dependencies on a repeated
                        bundle operation. By default, dependencies will remain
                        cached for the lifetime of the shell to speed up the
                        bundling process. This will force dependencies to be
                        installed even if they had been installed previously.
  --description DESCRIPTION
                        Specify a message to assign to the version published
                        by the deploy command.
  --dry-run             If set, the deploy operation will be exercised without
                        actually carrying out the actions. This can be useful
                        to validate the deploy process without side effects.

```

## region

Switches the target region.

```
usage: region
              [{us-east-2,us-east-1,us-west-1,us-west-2,af-south-1,ap-east-1,ap-south-1,ap-northeast-3,ap-northeast-2,ap-southeast-1,ap-southeast-2,ap-northeast-1,ca-central-1,cn-north-1,cn-northwest-1,eu-central-1,eu-west-1,eu-west-2,eu-south-1,eu-west-3,eu-north-1,me-south-1,sa-east-1,us-gov-east-1,us-gov-west-1}]

positional arguments:
  {us-east-2,us-east-1,us-west-1,us-west-2,af-south-1,ap-east-1,ap-south-1,ap-northeast-3,ap-northeast-2,ap-southeast-1,ap-southeast-2,ap-northeast-1,ca-central-1,cn-north-1,cn-northwest-1,eu-central-1,eu-west-1,eu-west-2,eu-south-1,eu-west-3,eu-north-1,me-south-1,sa-east-1,us-gov-east-1,us-gov-west-1}
                        AWS region name for the override. Leave it blank to
                        return to the default region for the initially loaded
                        credentials and/or environment variables.

```

## reload

Reloads the lambda.yaml configuration file from disk.

```
usage: reload

```

## select

Allows for selecting subsets of the targets within the loaded configuration.
The subsets are fuzzy-matched unless the --exact flag is used.

```
usage: select [--functions] [--layers] [--exact] [name [name ...]]

positional arguments:
  name                  Specifies the value to match against the function and
                        layer target names available from the configuration.
                        This can include shell-style wildcards and will also
                        match against partial strings. If the --exact flag is
                        specified, this value must exactly match one of the
                        targets instead of the default fuzzy matching
                        behavior.

optional arguments:
  --functions, --function, --func, -f
                        When specified, functions will be selected. This will
                        default to true if neither of --functions or --layers
                        is specified. Will default to false if --layers is
                        specified.
  --layers, --layer, -l
                        When specified, layers will be selected. This will
                        default to true if neither of --functions or --layers
                        is specified. Will default to false if --functions is
                        specified.
  --exact               Forces the match to be exact instead of fuzzy.

```

## shell

Special command to use in run command groups/macros to start interactive
command mode for the terminal. Useful when in scenarios where you wish to
prefix an interactive session with commonly executed commands. For example, if
you want to select certain targets with the select command as part of starting
the shell, you could create a run command group/macro in your lambda.yaml that
executes the select command and then executes the shell command. This would
updated the selection and then with the shell command, start the shell in
interactive mode. Without specifying the shell command here, the run command
group/macro would just set a selection and then exit.

```
usage: shell

```

## status

Shows the current status information for each of the selected lambda targets.

```
usage: status [qualifier]

positional arguments:
  qualifier  Specifies a version or alias to show status for. If not
             specified, $LATEST will be used for functions and the latest
             version will be dynamically determined for layers.

```
    
More detail on any of these commands can be found from within the shell by
executing them with the `--help` flag.

The reviser application also supports non-interactive batch command
execution via `run` macros that behave similarly to how `npm run <command>` 
commands are defined. For more details see the `run` attribute section of the
configuration file definitions below.

# Configuration Files

Configuration files, named `lambda.yaml` define the the lambda targets to be
managed within a project. The top-level keys in the configuration file are:

## bucket(s)

This key defines the bucket or buckets where zipped source bundles will be
uploaded before they are deployed to their lambda function and/or layer
targets. Basic usage is to specify the bucket as a key:

```yaml
bucket: bucket-name
```

It's also possible for multi-account scenarios to specify multiple buckets as
a key-value pairing where the keys are the AWS account IDs (as strings) and
the values are the bucket names associated with those IDs. In this case the
bucket selection is made dynamically based on the AWS session loaded during
shell initialization. Specifying multiple buckets looks like:

```yaml
buckets:
  "123456789": bucket-in-account-123456789
  "987654321": bucket-in-account-987654321
``` 

## AWS region

The AWS region in which the resources reside can be specified at the top
level of the file if desired. It is recommended that the region be specified
within the calling AWS profile if possible for flexibility, but there are
situations where it makes more sense to make it explicit within the 
configuration file instead. If no region is found either in the configuration
file or in the AWS profile the `us-east-1` region will be used as the default
in keeping with AWS region defaulting conventions. Specify the region with
the top-level key:

```yaml
region: us-east-2
```

## targets

Targets is where the bulk of the configuration resides. Each item
is either of the *function* or *layer* kind and has associated
configuration and bundling settings according to the type. Common
to both *function* and *layer* kinds are the keys:

### targets[N].kind

As mentioned already, each target must specify its object type using
the kind key:

```yaml
targets:
- kind: function
  ...
- kind: layer
  ...
```

### targets[N].name(s)

The name specifies the name of the target object, not the ARN. For example,
a function named foo would be represented as:

```yaml
targets:```  
- kind: function
  name: foo
```

A single target can point to multiple functions. This is useful in cases
where a single target could be for both development and production functions
or where a single code-base is shared across multiple functions for logical
or integration reasons. In this case a list of names is supplied instead:

```yaml
targets:
- kind: function
  names:
  - foo-devel
  - foo-prod
``` 

### targets[N].region

In the same fashion as regions can be explicitly set as a top-level
configuration key, they can also be set on a per-target basis. If set,
the target region will take precedence over the top-level value and
the profile-specified value. This makes deploying code across regions
within a single configuration file possible.

### targets[N].dependencies

Dependencies is a list of external dependency sources to install as
site packages in the lambda function or layer. Multiple package managers
are supported and specified by the `kind` attribute:

```yaml
targets:
- kind: layer
  name: foo
  dependencies:
  - kind: pip
  - kind: pipper
  - kind: poetry
```

Currently `pip`, `pipper` and `poetry` package managers are supported. For any of the
package managers, the dependencies can be specified explicitly with the 
`package(s)` key.

```yaml
targets:
- kind: layer
  name: foo
  dependencies:
  - kind: pip
    packages: 
    - spam
    - hamd
  - kind: pipper
    package: spammer
```

It's also possible to specify a file to where the package dependencies
have been defined.

```yaml
targets:
- kind: layer
  name: foo
  dependencies:
  - kind: pip
    file: requirements.layer.txt
  - kind: pipper
    file: pipper.layer.json
```

If no packages or file is specified, the default file for the given package
manager will be used by default (e.g. `requirements.txt` for pip,
 `pipper.json` for pipper, and `pyproject.toml` for poetry).

It is also possible to specify the same kind of package manager multiple
times in this list to aggregate dependencies from multiple locations.

### targets[N].dependencies(kind="pipper")

Pipper repositories have additional configuration not associated with pip
packages. To support pipper libraries, there are two additional attributes
that can be specified: `bucket` and `prefix`.

The `bucket` is required as it specifies the S3 bucket used as the package
source and should be read-accessible by the profile invoking reviser.

The `prefix` is an optional alternate package prefix within the S3 bucket.
Use this only if you are using an alternate prefix with for your pipper
package.

```yaml
targets:
- kind: layer
  name: foo
  dependencies:
  - kind: pipper
    file: pipper.layer.json
    bucket: bucket-name-where-pipper-package-resides
    prefix: a/prefix/that/is/not/just/pipper
```

### targets[N].dependencies(kind="poetry")

Poetry repositories have additional `extras` configuration that can be used to
specify optional dependency groups to install in the lambda. This can be useful
to separate dependencies by function.

```yaml
targets:
- kind: layer
  name: foo
  dependencies:
  - kind: poetry
    extras:
    - group
```

### targets[N].bundle

The target bundle object contains the attributes that define the bundle
that will be created and uploaded to the functions or layers in a given
target as part of the deployment process. It's primary purpose is to define
what files should be included in the bundling process, which it achieves
with the following attributes.

#### targets[N].bundle.include(s)

The `include(s)` key is a string or list of Python glob-styled includes
to add to the bundle. If no includes are specified, the default behavior is:

- **function targets**: copy the first directory found that contains an 
  *__init__.py* file.
- **layer targets**: do not copy anything and assume dependencies are the
  only files to copy into the bundle.

All paths should be referenced relative to the root path where the
`lambda.yaml` is located. For a recursive matching pattern, the glob syntax
should be used as `**/*.txt` or if restricted to a folder inside of the root
directory then `folder/**/*.txt`. To include the entire contents of a
directory, specify the path to the folder.

```yaml
targets:
- kind: function
  name: foo
  bundle:
    includes:
    # This is shorthand for "foo_library/**/*"
    - foo_library
    # All Python files in the "bin/" folder recursively.
    - bin/**/*.py
    # All Jinja2 files in the root directory that begin "template_".
    - template_*.jinja2
```

#### targets[N].bundle.exclude(s)

The `exclude(s)` key is an optional one that is also a string or list of
Python glob-styled paths to remove from the matching `include(s)`. These
are applied to the files found via the includes and do not need to be
comprehensive of all files in the root directory. Building on the example
from above:

```yaml
targets:
- kind: function
  name: foo
  bundle:
    includes:
    # This is shorthand for "foo_library/**/*"
    - foo_library
    # All Python files in the "bin/" folder recursively.
    - bin/**/*.py
    # All Jinja2 files in the root directory that begin "template_".
    - template_*.jinja2
    exclues:
    - template_local.jinja2
    - template_testing.jinja2
```

This example would remove two of the template file matches from the includes
from the files copied into the bundle for deployment.

All `__pycache__`, `*.pyc` and `.DS_Store` files/directories are
excluded from the copying process in all cases and do not need to be 
specified explicitly.

#### targets[N].bundle.omit_package(s)

There can be cases where dependencies install dependencies of their own that
you may not want copied over to the bundle. The most common case is a
dependency that requires `boto3`, which is available by default in lambda
functions already. In that case it can be useful to list site packages that
should not be copied into the bundle but may have been installed as a side
effect of the dependency installation process.

```yaml
targets:
- kind: function
  name: foo
  bundle:
    omit_package: boto3
  dependencies:
  - kind: pip
    # Installs a package that requires boto3, which is therefore installed
    # into the site-packages bundle directory as a result.
    # https://github.com/awslabs/aws-lambda-powertools-python
    package: aws-lambda-powertools
```

In the above example `aws-lambda-powertools` causes `boto3` to be installed
as well. However, since lambda functions have `boto3` installed by default,
it's possible to omit that package from the bundling process so that it isn't
installed twice.

Note, however, that installing `boto3` directly in a bundle can be beneficial
because it gives you the ability to install the version that is compatible
with your given source code and dependencies. The `boto3` version on the lambda
function can be aged and stale.

#### targets[N].bundle.handler

This attribute only applies to function targets and gives the location of
file and function entrypoint for the lambda function(s) in the target. The
format matches the expected value for lambda functions, which is 
`<filename_without_extension>.<function_name>`.

```yaml
targets:
- kind: function
  name: foo
  bundle:
    handler: function:main
```

In this case the bundler would expect to find `function.py` in the top-leve
directory alongside `lambda.yaml` and inside it there would be a 
`main(event, context)` function that would be called when the function(s)
are invoked.

If this value is omitted, the default value of `lambda_function.lambda_handler`
will be used as this matches the AWS lambda Python function documentation.

## function targets

In addition to the common attributes described above that are shared between
both function and layer targets, there are a number of additional
attributes that apply only to function targets. These are:

### (function) targets[N].layer(s)

Specifies one or more layers that should be attached to the targeted
function(s). Layers can be specified as fully-qualified ARNs for externally
specified layers, e.g. a layer created in another AWS account, or by name
for layers specified within the account and layers defined within the targets
of the configuration file.

```yaml
targets:
- kind: function
  name: foo
  layer: arn:aws:lambda:us-west-2:999999999:layer:bar
  ...
```

or for multiple layers:

```yaml
targets:
- kind: function
  name: foo
  layers:
  # A layer defined in another account is specified by ARN.
  - arn:aws:lambda:us-west-2:999999999:layer:bar
  # A layer in this account is specified by name. This layer may also be
  # a target in this configuration file.
  - baz
  ...
- kind: layer
  name: baz
  ...
```

By default, deployments will use the latest available version of each layer,
but this can be overridden by specifying the layer ARN with its version:

```yaml
targets:
- kind: function
  name: foo
  layer: arn:aws:lambda:us-west-2:999999999:layer:bar:42
  ...
```

In the above example the layer will remain at version 42 until explicitly
modified in the configuration file.

Layers can also be defined as objects instead of attributes. The two-layer
example from above could be rewritten as:

```yaml
targets:
- kind: function
  name: foo
  layers: 
  - arn: arn:aws:lambda:us-west-2:999999999:layer:bar
  - name: baz
  ...
```

When specified as an object with attributes, there are a number of additional
attributes that can be specified as well. First, `version` can be specified
as a separate key from the arn or name, which in many cases can make it easier
to work with than appending it to the end of the arn or function itself for
programmatic/automation:

```yaml
targets:
- kind: function
  name: foo
  layers: 
  - arn: arn:aws:lambda:us-west-2:999999999:layer:bar
    version: 42
  - name: baz
    version: 123
  ...
```

Next is that the layer objects accept `only` and `except` keys that can be
used to attach the layers to certain functions in the target and not others.
This can be useful in cases where development and production targets share
a lot in common, but perhaps point to different versions of a layer or perhaps
separate development and production layers entirely. It can also be useful
when a target of functions share a common codebase but don't all need the
same dependencies. For performance optimization, restricting the layer 
inclusions only to those that need the additional dependencies can be
beneficial.

The `only` and `except` attributes can be specified as a single string
or a list of strings that match against *unix pattern matching*. For example,
expanding on the example from above:

```yaml
targets:
- kind: function
  names: 
  - foo-devel
  - foo-devel-worker
  - foo-prod
  - foo-prod-worker
  layers: 
  - name: baz-devel
    only: foo-devel*
  - name: baz-devel-worker
    only: foo-devel-worker
  - name: baz-prod
    only: foo-prod*
  - name: baz-prod-worker
    only: foo-prod-worker
  ...
```

this example shows 4 layers that are conditionally applied using the only
keyword. The example could be rewritten with the `except` key instead:

```yaml
targets:
- kind: function
  names: 
  - foo-devel
  - foo-devel-worker
  - foo-prod
  - foo-prod-worker
  layers: 
  - name: baz-devel
    except: foo-prod*
  - name: baz-devel-worker
    except:
    - foo-prod*
    - foo-devel
  - name: baz-prod
    except: foo-devel*
  - name: baz-prod-worker
    except:
    - foo-devel*
    - foo-prod
  ...
```

And either way works. The two (`only` and `except`) can also be combined
when that makes more sense. For example, the `baz-devel-worker` from above
could also be written as:

```yaml
  - name: baz-devel-worker
    only: foo-devel*
    except: foo-devel
```

Note that if `only` is specified it is processed first and then `except` is
removed from the matches found by `only`. 

### (function) targets[N].memory

This specifies the function memory in megabytes either as an integer or
a string with an `MB` suffix.

```yaml
targets:
- kind: function
  name: foo
  memory: 256MB 
```

### (function) targets[N].timeout

This specifies the function timeout in seconds either as an integer or
a string with an `s` suffix.

```yaml
targets:
- kind: function
  name: foo
  timeout: 42s 
```

### (function) targets[N].variable(s)

Variables contains a list of environment variables to assign to the function.
They can be specified simply with as a string `<KEY>=<value>` syntax:

```yaml
targets:
- kind: function
  name: foo
  variable: MODE=read-only
```

Here a single environment variable is specified that maps `"MODE"` to the
value *"ready-only"*. A more programmatic-friendly way is to specify the
name and value as attributes of a variable:

```yaml
targets:
- kind: function
  name: foo
  variables: 
  - name: MODE
    value: read-only
```

Some environment variables may be managed through other means, e.g. 
terraform that created the function in the first place or another command
interface used to update the function. For those cases, the `preserve`
attribute should be set to true and no value specified.

```yaml
targets:
- kind: function
  name: foo
  variables: 
  - name: MODE
    preserve: true
```

In this case the `MODE` environment variable value will be preserved between
function deployments to contain the value that was already set.

Finally, variables support the same `only` and `exclude` attributes that
are found for target layers so that environment variables can be specified
differently for subsets of targets.

The `only` and `except` attributes can be specified as a single string
or a list of strings that match against *unix pattern matching*. For example,
expanding on the example from above:

```yaml
targets:
- kind: function
  names: 
  - foo-prod
  - foo-devel
  variables: 
  - name: MODE
    value: write
    only: '*prod'
  - name: MODE
    value: read-only
    except: '*prod'
```

### (function) targets[N].ignore(s)

Ignores allows you to specify one or more configuration keys within a function
target that should be ignored during deployments. For cases where any of the 
configuration values:

- `memory`
- `timeout`
- `variables`

are managed by external systems, they can be specified by the ignores to
prevent changes being applied by reviser.

```yaml
targets:
- kind: function
  name: foo
  ignores:
  - memory
  - timeout
```

## run

The run attribute contains an optional object of batch non-interactive commands
to run when the shell is called with that run key. This is useful for 
orchestrating actions for CI/CD purposes as the commands will be processed
within a shell environment without user prompts and then the shell will exit
when complete without waiting for additional input.

```yaml
run:
  deploy-prod:
  - select function *prod 
  - push --description="($CI_COMMIT_SHORT_SHA): $CI_COMMIT_TITLE"
  - alias test -1
targets:
- kind: function
  names:
  - foo-prod
  - foo-devel
```

In the example above, the `deploy-prod` run command macro/group would start
the shell and then non-interactively execute the three commands in order
to first select the *foo-prod* function, then to build and deploy that function
with a description created from CI environment variables and finally move the
*test* alias to the newly deployed version using a negative version index of
*-1*. After those three commands are executed reviser will exit the
shell automatically, successfully ending that process.

There is also a special `shell` command that can be used in run command
macros/groups that will start the shell in interactive mode. This is useful
for using run command macros/groups for pre-configuration during startup of
the interactive shell. Building on the previous example,

```yaml
run:
  deploy-prod:
  - select function *prod 
  - push --description="($CI_COMMIT_SHORT_SHA): $CI_COMMIT_TITLE"
  - alias test -1
  devel:
  - select * *devel
  - bundle
  - shell
targets:
- kind: function
  names:
  - foo-prod
  - foo-devel
- kind: layer
  names:
  - bar-devel
  - bar-prod
```

here we've added a `devel` run command macro/group that will select the devel
function and layer and bundle those but not deploy them. After that's complete
the shell command will kick off the interactive session and ask for user
input. The benefit of this particular run command macro/group is to select
the development targets and pre-build them to cache the dependencies for the
shell user while they continue to develop and deploy the source code to the
function.



# Local Execution

When running reviser in your current environment instead of launching the shell within
a new container, you will want to use the command `reviser-shell`. This is the local
version of the CLI that is meant to be used within a suitable container environment
that mimics the lambda runtime environment. It is merely a change in entrypoint, and
has all the shell functionality described for the `reviser` command above.

Also, to run the `reviser-shell` successfully, you must install the extra shell
dependencies with the installation:

```shell
$ pip install reviser[shell]
```

Without the shell extras install, the `reviser-shell` will fail. This is how you would
use reviser in a containerized CI environment as well.