# Configuration Files

Configuration files, named `lambda.yaml` define the lambda targets to be
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

Multiple region buckets can also be specified using the AWS region as the key:

```yaml
buckets:
  us-east-1: bucket-in-region-us-east-1
  us-west-2: bucket-in-region-us-west-2
```

These can be combined to define buckets for multiple accounts and multiple
regions as:


```yaml
buckets:
  "123456789":
    us-east-1: bucket-123456789-in-region-us-east-1
    us-west-2: bucket-123456789-in-region-us-west-2
  "987654321":
    us-east-1: bucket-987654321-in-region-us-east-1
    us-west-2: bucket-987654321-in-region-us-west-2
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
