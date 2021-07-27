"""Switch the target region."""
import argparse
import typing

from reviser import interactivity

# https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.RegionsAndAvailabilityZones.html  # noqa
AVAILABLE_REGIONS = {
    "us-east-2": "US East (Ohio)",
    "us-east-1": "US East (N. Virginia)",
    "us-west-1": "US West (N. California)",
    "us-west-2": "US West (Oregon)",
    "af-south-1": "Africa (Cape Town)",
    "ap-east-1": "Asia Pacific (Hong Kong)",
    "ap-south-1": "Asia Pacific (Mumbai)",
    "ap-northeast-3": "Asia Pacific (Osaka-Local)",
    "ap-northeast-2": "Asia Pacific (Seoul)",
    "ap-southeast-1": "Asia Pacific (Singapore)",
    "ap-southeast-2": "Asia Pacific (Sydney)",
    "ap-northeast-1": "Asia Pacific (Tokyo)",
    "ca-central-1": "Canada (Central)",
    "cn-north-1": "China (Beijing)",
    "cn-northwest-1": "China (Ningxia)",
    "eu-central-1": "Europe (Frankfurt)",
    "eu-west-1": "Europe (Ireland)",
    "eu-west-2": "Europe (London)",
    "eu-south-1": "Europe (Milan)",
    "eu-west-3": "Europe (Paris)",
    "eu-north-1": "Europe (Stockholm)",
    "me-south-1": "Middle East (Bahrain)",
    "sa-east-1": "South America (São Paulo)",
    "us-gov-east-1": "AWS GovCloud (US-East)",
    "us-gov-west-1": "AWS GovCloud (US-West)",
}


def get_completions(
    completer: "interactivity.ShellCompleter",
) -> typing.List[str]:
    """Get shell auto-completes for this command."""
    return list(AVAILABLE_REGIONS.keys())


def populate_subparser(parser: argparse.ArgumentParser):
    """Populate parser for this command."""
    parser.add_argument(
        "region_name",
        choices=list(AVAILABLE_REGIONS.keys()),
        nargs="?",
        help="""
            AWS region name for the override. Leave it blank to return to
            the default region for the initially loaded credentials and/or
            environment variables.
            """,
    )


def run(ex: "interactivity.Execution") -> "interactivity.Execution":
    """Switch the configured region for the shell."""
    region_name = ex.args.get("region_name")
    configs = ex.shell.context.configuration

    if not region_name and "region" in configs.data:
        del configs.data["region"]
    elif region_name:
        configs.data["region"] = region_name

    return ex.finalize(
        status="SWITCHED_REGION",
        message=f"Now in region {configs.aws_region}.",
        echo=True,
        data={"region": configs.aws_region},
    )
