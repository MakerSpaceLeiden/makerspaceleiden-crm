from django.urls import reverse

from makerspaceleiden.templatetags.isingroup import (
    isInPettycashAdmin,
    isMainsAdmin,
    isNoderedAdmin,
    isTreasurer,
)


def get_trustee_links(user):
    trustee_links = []
    if user is None:
        return trustee_links

    # Privileged user links
    if user.is_authenticated and getattr(user, "is_privileged", True):
        trustee_links += [
            {"url": reverse("admin:index"), "label": "Raw database access"},
            {"url": reverse("newmember"), "label": "Add a new member"},
            {"url": reverse("pending"), "label": "Instructions pending approval"},
            {"url": reverse("missing_doors"), "label": "Missing doors or tags"},
            {"url": reverse("missing_forms"), "label": "Missing waivers"},
            {"url": reverse("filed_forms"), "label": "Filed waivers"},
            {"url": reverse("unknowntags"), "label": "Unknown tags"},
            {"url": reverse("acl-index"), "label": "Permit use"},
            {"url": reverse("cam53upload"), "label": "Upload Triodos transactions"},
            {
                "url": reverse("mailinglists_subs"),
                "label": "Members mailing list subscriptions",
            },
        ]

    # MainsAdmin or privileged
    is_mains_admin = getattr(user, "is_privileged", True) or isMainsAdmin(user)
    if user.is_authenticated and is_mains_admin:
        trustee_links += [
            {"url": reverse("mainsindex"), "label": "Lucas MainsSensors"},
            {
                "url": "/api/v1/mainssensor/resolve",
                "label": "Lucas MainsSensors resolved",
            },
        ]

    # PettycashAdmin, Treasurer, or privileged
    is_pettycash_admin = getattr(user, "is_privileged", True) or isInPettycashAdmin(
        user
    )
    is_treasurer = getattr(user, "is_privileged", True) or isTreasurer(user)
    if user.is_authenticated and (is_pettycash_admin or is_treasurer):
        trustee_links.append({"url": reverse("unpaired"), "label": "Payment stations"})

    # NoderedAdmin or privileged
    is_nodered_admin = getattr(user, "is_privileged", True) or isNoderedAdmin(user)
    if user.is_authenticated and is_nodered_admin:
        trustee_links.append(
            {"url": reverse("nodered_proxy", args=[""]), "label": "Node-Red editor"}
        )

    return trustee_links


def navbar_links(request):
    user = request.user
    trustee_links = get_trustee_links(user)

    return {
        "navbar_links": {
            "public": {
                "label": "Wiki & Public Info",
                "children": [
                    {
                        "url": "https://wiki.makerspaceleiden.nl/",
                        "label": "Wiki documentation",
                    },
                    {
                        "url": "https://wiki.makerspaceleiden.nl/mediawiki/index.php/Categorie:Tools",
                        "label": "Tools",
                    },
                    {
                        "url": "https://wiki.makerspaceleiden.nl/mediawiki/index.php/Categorie:Projects",
                        "label": "Projects",
                    },
                    {
                        "url": "https://wiki.makerspaceleiden.nl/mediawiki/index.php/Makerspace_Leiden#Veiligheid_en_geluidsproductie",
                        "label": "Safety and noise production",
                    },
                    {
                        "url": "https://wiki.makerspaceleiden.nl/mediawiki/index.php/Makerspace_Leiden#Procedures_en_Principes",
                        "label": "Procedures and principles",
                    },
                    {
                        "url": "https://wiki.makerspaceleiden.nl/mediawiki/index.php/Create_a_new_wiki_page",
                        "label": "Create a new wiki",
                    },
                    {"url": "https://github.com/MakerSpaceLeiden", "label": "GitHub"},
                    {
                        "url": "https://wiki.makerspaceleiden.nl/mediawiki/index.php/About_Makerspace",
                        "label": "About Us",
                    },
                ],
            },
            "events": {
                "label": "Current Events",
                "children": [
                    {"url": reverse("space_state"), "label": "Who is there now"},
                    {
                        "url": reverse("nodered_active_machines"),
                        "label": "Active machines",
                    },
                    {
                        "url": reverse("nodered_live_data_and_sensors"),
                        "label": "Live data & sensors",
                    },
                    {"url": reverse("agenda"), "label": "Agenda"},
                    {"url": reverse("motd_messages"), "label": "Message of the day"},
                    {"url": reverse("ufo"), "label": "UFO lost and found"},
                    {"url": reverse("camindex"), "label": "Live 3D printer camera"},
                    {"url": reverse("kwh_view"), "label": "Power consumption"},
                ],
            },
            "community": {
                "label": "Machines & Community",
                "children": [
                    {"url": reverse("overview"), "label": "All members"},
                    {"url": reverse("machine_list"), "label": "Machines"},
                    {"url": reverse("chores"), "label": "Chores"},
                    {"url": reverse("add_instruction"), "label": "Record instructions"},
                    {"url": reverse("mytransactions"), "label": "SpaceTegoed"},
                    # Only add 'Pay for a product' if user is authenticated
                    *(
                        [
                            {
                                "url": reverse(
                                    "invoice", kwargs={"src": request.user.id}
                                ),
                                "label": "Pay for a product",
                            }
                        ]
                        if request.user.is_authenticated
                        else []
                    ),
                    {"url": reverse("boxes"), "label": "Member boxes"},
                ],
            },
            "profile": {
                "label": "Profile Settings",
                "children": [
                    {"url": reverse("personal_page"), "label": "Personal profile"},
                    {"url": reverse("userdetails"), "label": "Change personal details"},
                    {"url": reverse("password_change"), "label": "Change password"},
                    {"url": reverse("mytransactions"), "label": "Cash balance"},
                    {
                        "url": reverse("mailinglists_edit"),
                        "label": "Mailing lists subscriptions",
                    },
                    {"url": reverse("notification_settings"), "label": "Notifications"},
                    {"url": reverse("boxes"), "label": "Member box"},
                ],
            },
            "trustee": {
                "label": "Trustee",
                "children": trustee_links,
            },
        }
    }
