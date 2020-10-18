# Reviser (v{{ version }})

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
{{ shell_commands_toc }}
{{ configuration_toc }}

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

{{ shell_commands }}
    
More detail on any of these commands can be found from within the shell by
executing them with the `--help` flag.

The reviser application also supports non-interactive batch command
execution via `run` macros that behave similarly to how `npm run <command>` 
commands are defined. For more details see the `run` attribute section of the
configuration file definitions below.

{{ configuration }}
