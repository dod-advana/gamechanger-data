import os


def get_placeholder() -> str:
    """Returns empty string in PROD and lorem ipsum... otherwise"""

    deployment_env = os.environ.get("DEPLOYMENT_ENV", "").lower()
    if deployment_env == "prod":
        return ""
    return (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Vestibulum sodales urna massa. "
        "Integer id lorem nec felis hendrerit sagittis non nec arcu. "
        "Curabitur maximus lacus est, et rhoncus lorem ultricies sed. "
        "Curabitur ultricies, metus ac placerat viverra, mauris libero mollis diam, "
        "et fringilla libero metus in ipsum. "
        "In interdum molestie velit, in efficitur tellus tincidunt eu. "
        "Sed bibendum elementum quam, quis tempus tortor pretium quis. "
        "Nam mattis magna volutpat ante auctor, sed varius magna interdum. "
        "Nam vel arcu eget orci faucibus aliquet. "
        "Aenean velit massa, varius a lectus id, tincidunt lacinia magna. "
        "Interdum et malesuada fames ac ante ipsum primis in faucibus. "
        "Duis tristique mollis fermentum. Quisque id posuere diam. "
        "Duis vitae gravida lorem. Pellentesque sed odio commodo felis ultrices posuere in vel mi."
    )


def add_summary(doc_dict):
    """Add summary_30 field to doc dict"""
    summary = get_placeholder()
    doc_dict["summary_30"] = summary
    return doc_dict
