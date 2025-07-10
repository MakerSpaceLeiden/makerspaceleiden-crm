from django.urls import reverse

def navbar_links(request): 
    return {
       "navbar_links" : {
            "public": {
            "label": "Wiki & Public Info",
            "children": [
                {"url": "https://wiki.makerspaceleiden.nl/", "label": "Wiki documentation"},
                {"url": "https://wiki.makerspaceleiden.nl/mediawiki/index.php/Categorie:Tools", "label": "Tools"},
                {"url": "https://wiki.makerspaceleiden.nl/mediawiki/index.php/Categorie:Projects", "label": "Projects"},
                {"url": "https://wiki.makerspaceleiden.nl/mediawiki/index.php/Makerspace_Leiden#Veiligheid_en_geluidsproductie", "label": "Safety and noise production"},
                {"url": "https://wiki.makerspaceleiden.nl/mediawiki/index.php/Makerspace_Leiden#Procedures_en_Principes", "label": "Procedures and principles"},
                {"url": "https://wiki.makerspaceleiden.nl/mediawiki/index.php/Create_a_new_wiki_page", "label": "Create a new wiki"},
                {"url": "https://github.com/MakerSpaceLeiden", "label": "GitHub"},
                {"url": "https://wiki.makerspaceleiden.nl/mediawiki/index.php/About_Makerspace", "label": "About Us"},
            ]
        },
        "another": {
            "label": "Another", 
            "children": [
                
            ]
        },
        "events": {
            "label": "Current Events",
            "children": [
                {"url": reverse("space_state"), "label": "Who is there now"},
                {"url": reverse("nodered_active_machines"), "label": "Active machines"},
                {"url": reverse("nodered_live_data_and_sensors"), "label": "Live data & sensors"},
                {"url": reverse("agenda"), "label": "Agenda"},
                {"url": reverse("motd_messages"), "label": "Message of the day"},
                {"url": reverse("ufo"), "label": "UFO lost and found"},
                {"url": reverse("camindex"), "label": "Live 3D printer camera"},
                {"url": reverse("kwh_view"), "label": "Power consumption"},
            ]
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
                *( [{"url": reverse("invoice", kwargs={"src": request.user.id}), "label": "Pay for a product"}] if request.user.is_authenticated else [] ),
                {"url": reverse("boxes"), "label": "Member boxes"},
            ]
        },
        "profile": {
            "label": "Profile Settings",
            "children": [
                {"url": reverse("personal_page"), "label": "Personal profile"},
                {"url": reverse("userdetails"), "label": "Change personal details"},
                {"url": reverse("password_change"), "label": "Change password"},
                {"url": reverse("mytransactions"), "label": "Cash balance"},
                {"url": reverse("mailinglists_edit"), "label": "Mailing lists subscriptions"},
                {"url": reverse("notification_settings"), "label": "Notifications"},
                {"url": reverse("boxes"), "label": "Member box"},
            ]
        }
       }
    }