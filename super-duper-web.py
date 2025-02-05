import csv
import re
import flet as ft
from flet import FilePickerResultEvent
import requests
import json
import os 
import tempfile
from datetime import datetime
#####################################################


# Page 1: Splash Page

def page1(page: ft.Page):
    page.title = "Title Page"


    # Centered title with space from the top
    spacer = ft.Container(height=50)
    title = ft.Text("Super Duper CSV to DOI to CSV App", size=36, weight="bold", color=ft.Colors.PINK_100)

    # Numbered list
    list_items = [
        "1. DSpace to Datacite CSV Converter",
        "2. Datacite Bulk DOI Creator",
        "3. CSV Merger for DSpace Import",
        "4. Statistics",
        "5: Visit the repo . . . ",
        
    ]
    list_view = ft.ListView(
        expand=True,
        spacing=5,
        padding=10,
        auto_scroll=True,
        controls=[ft.Text(item, size=14) for item in list_items]
    )

    # Navigation link to Page 2 (lower right)
    nav_link = ft.Row(
        [
            ft.TextButton("DSPACE TO DATACITE CSV CONVERTER →", on_click=lambda _: navigate_to_page2(page)),
        ],
        alignment=ft.MainAxisAlignment.END,
    )

    page.add(
        spacer,
        title,
        list_view,
        nav_link
    )

#####################################################

# Page 2: DSpace to Datacite CSV Converter


def reverse_name_order(name):
    """Reverse the order of a name formatted as 'LASTNAME, FIRSTNAME' and strip trailing periods."""
    parts = [part.strip().rstrip(".") for part in name.split(",")]
    if len(parts) == 2:
        return f"{parts[1]} {parts[0]}"
    return name.strip().rstrip(".")

def map_type(dspace_type, type_mapping):
    """Map DSpace types to Datacite types."""
    #default if no mapping is defined
    return type_mapping.get(dspace_type, "Unknown") 

def process_csv(dspace_csv, datacite_csv, type_mapping, progress, log):
    uri_patterns = ["http://hdl.handle.net/10613", "http://hdl.handle.net/10170"]

    try:
        with open(dspace_csv, mode="r", encoding="utf-8") as dspace_file:
            dspace_reader = csv.DictReader(dspace_file)

            datacite_fieldnames = [
                "title", "year", "type", "description",
                "creator1", "creator1_type", "creator1_given", "creator1_family",
                "creator2", "creator2_type", "creator2_given", "creator2_family",
                "publisher", "source"
            ]

            datacite_rows = []
            input_row_count = 0
            output_row_count = 0

            for row in dspace_reader:
                input_row_count += 1
                progress.value = input_row_count
                progress.update()

                title = row.get("dc.title[en]", row.get("dc.title", row.get("dc.title[]", ""))).strip()
                year = row.get("dc.date.issued[]", row.get("dc.date.issued[en]", row.get("dc.date.issued", ""))).strip()
                type_field = map_type(row.get("dc.type[en]", row.get("dc.type", row.get("dc.type[]", ""))).strip(), type_mapping)
                description = row.get("dc.description.abstract[en]", row.get("dc.description", row.get("dc.description[]", ""))).strip()
                publisher = row.get("dc.publisher[en]", "").strip()

                source = ""
                for uri_field in ["dc.identifier.uri[]", "dc.identifier.uri", "dc.identifier.uri[en]"]:
                    if uri_field in row and any(pattern in row[uri_field] for pattern in uri_patterns):
                        source = row[uri_field].split("||")[0].strip()
                        break

                contributors = []

                def get_field_data(row, base_field_name):
                    for suffix in ["[en]", "[]", ""]:
                        value = row.get(f"{base_field_name}{suffix}", "").strip()
                        if value:
                            return value
                    return ""

                for field_group in ["author", "other", "editor", "advisor"]:
                    field_data = get_field_data(row, f"dc.contributor.{field_group}")
                    if field_data:
                        contributors.extend([
                            re.sub(r"::.*", "", name).strip().rstrip(".")
                            for name in field_data.split("||") if name.strip()
                        ])

                if len(contributors) == 0:
                    creator1, creator2 = "Unknown", ""
                else:
                    creator1 = reverse_name_order(contributors[0])
                    creator2 = reverse_name_order(contributors[1]) if len(contributors) > 1 else ""

                def split_name(name):
                    parts = name.split()
                    if len(parts) > 1:
                        return " ".join(parts[:-1]), parts[-1]
                    return "", name

                creator1_given, creator1_family = split_name(creator1 if creator1 != "Unknown" else "")
                creator2_given, creator2_family = split_name(creator2)

                datacite_rows.append({
                    "title": title,
                    "year": year,
                    "type": type_field,
                    "description": description,
                    "creator1": creator1,
                    "creator1_type": "Personal" if creator1 != "Unknown" else "",
                    "creator1_given": creator1_given,
                    "creator1_family": creator1_family,
                    "creator2": creator2,
                    "creator2_type": "Personal" if creator2 else "",
                    "creator2_given": creator2_given,
                    "creator2_family": creator2_family,
                    "publisher": publisher,
                    "source": source
                })
                output_row_count += 1

        with open(datacite_csv, mode="w", encoding="utf-8", newline="") as datacite_file:
            writer = csv.DictWriter(datacite_file, fieldnames=datacite_fieldnames)
            writer.writeheader()
            writer.writerows(datacite_rows)

        log.controls.append(ft.Text(f"\nTransformed data saved to {datacite_csv}\nRows in input file: {input_row_count}\nRows in output file: {output_row_count}", selectable=True))
        log.update()
    except Exception as e:
        log.controls.append(ft.Text(f"\nError: {str(e)}", selectable=True))
        log.update()

def page2(page: ft.Page):
    page.title = "DSpace to Datacite CSV Converter"

    header = ft.Text("DSpace to Datacite CSV Converter", size=24, weight="bold", color=ft.Colors.PINK_100)
    description = ft.Text(
        "Convert DSpace metadata export CSV into a Datacite compatible CSV format. Edit & save type mappings as needed",
        size=14,
        color=ft.Colors.GREY_600,
    )
    spacer = ft.Container(height=10)

    dspace_csv = ft.TextField(label="DSpace Export CSV File", disabled=True, width=500)
    datacite_filename = ft.TextField(
        label="Output Filename",
        label_style=ft.TextStyle(color=ft.Colors.BLUE), 
        height=40, 
        width=500, 
        hint_text="DataciteImport.csv",
        value="DataciteImport.csv"
    )
    output_directory = ft.TextField(
        label="Save Location",
        disabled=True,
        width=500
    )
    type_mapping_display = ft.TextField(label="Type Mapping", multiline=True, width=500)
    log = ft.ListView(expand=True, spacing=5, padding=10, auto_scroll=True)
    progress = ft.ProgressBar(width=500, visible=False)

    type_mapping = {
        "Article": "Text",
        "Book": "Text",
        "Thesis": "Text",
        "Dataset": "Dataset",
        "Image": "Image",
        "Video": "Audiovisual",
        "Audio": "Sound",
        "Other": "Other",
        "Illustrator": "Image",
        "Archival Material":"Text"
    }
    type_mapping_display.value = json.dumps(type_mapping, indent=4)

    def pick_dspace_file(e: FilePickerResultEvent):
        if e.files:
            dspace_csv.value = e.files[0].path
            dspace_csv.update()

    def pick_save_location(e: FilePickerResultEvent):
        if e.path:
            output_directory.value = e.path
            output_directory.update()

    def save_type_mapping(e):
        try:
            nonlocal type_mapping
            type_mapping = json.loads(type_mapping_display.value)
            with open("type_mapping.json", "w") as file:
                json.dump(type_mapping, file, indent=4)
            log.controls.append(ft.Text("Type mapping saved successfully!", selectable=True))
            log.update()
        except Exception as ex:
            log.controls.append(ft.Text(f"Error saving type mapping: {ex}", selectable=True))
            log.update()

    def start_conversion(e):
        if not dspace_csv.value or not datacite_filename.value or not output_directory.value or not type_mapping:
            log.controls.append(ft.Text("\nPlease select all required files and specify output location.", selectable=True))
            log.update()
            return

        progress.visible = True
        progress.update()

        # Combine directory and filename
        output_path = os.path.join(output_directory.value, datacite_filename.value)
        
        try:
            if page.web:
                # For web, we'll first save to a temporary file
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
                process_csv(dspace_csv.value, temp_file.name, type_mapping, progress, log)
                
                # Then trigger the download
                with open(temp_file.name, 'rb') as f:
                    page.client_storage.set('download_data', f.read())
                    page.launch_url(f"/download/{os.path.basename(output_path)}")
                
                # Clean up the temporary file
                os.unlink(temp_file.name)
            else:
                # For local app, save directly to the specified location
                process_csv(dspace_csv.value, output_path, type_mapping, progress, log)
        except Exception as e:
            log.controls.append(ft.Text(f"\nError during conversion: {str(e)}", selectable=True))
            log.update()

        progress.visible = False
        progress.update()

    pick_dspace_file_picker = ft.FilePicker(on_result=pick_dspace_file)
    save_location_picker = ft.FilePicker(
        on_result=pick_save_location
    )
    
    page.overlay.extend([pick_dspace_file_picker, save_location_picker])

    nav_link = ft.Row(
        [
            ft.TextButton("← START PAGE", on_click=lambda _: navigate_to_page1(page)),
            ft.TextButton("DATACITE BULK DOI CREATOR →", on_click=lambda _: navigate_to_page3(page)),
            
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    file_controls = ft.Column([
        dspace_csv,
        ft.ElevatedButton(
            "Select DSpace Export CSV",
            on_click=lambda _: pick_dspace_file_picker.pick_files(allow_multiple=False,allowed_extensions=["csv"])
        ),
        # Add space above Output Filename
        ft.Container(height=10),
        datacite_filename,  # Move Output Filename above Save Location
        output_directory,
        ft.ElevatedButton(
            "Choose Save Location",
            on_click=lambda _: save_location_picker.get_directory_path()
        ),
        ft.Container(height=15),
    ])

    page.add(
        header,
        description,
        spacer,
        file_controls,
        
        type_mapping_display,
        ft.ElevatedButton("Save Type Mapping", on_click=save_type_mapping),
        ft.ElevatedButton("Start Conversion", on_click=start_conversion),
        progress,
        log,
        nav_link
    )

#####################################################

# Page 3: DOI Generator and Config Editor

def page3(page: ft.Page):
    page.title = "DOI Creator and Config Editor"

    # Add header and description
    header = ft.Text("DataCite Bulk DOI Creator", size=24, weight="bold", color=ft.Colors.PINK_100)
    description = ft.Text(
        "Generate DOIs in bulk using DataCite. Upload a credentials file to proceed, and upload the CSV file you converted in the previous step.",
        size=14,
        color=ft.Colors.GREY_600,
    )
    spacer = ft.Container(height=10)

    # Config inputs (disabled for manual input)
    url_input = ft.TextField(label="DataCite URL", width=500, hint_text="https://api.datacite.org/dois", disabled=True)
    doi_prefix_input = ft.TextField(label="DOI Prefix", width=500, hint_text="10.12345", disabled=True)
    username_input = ft.TextField(label="Username", width=500, disabled=True)
    password_input = ft.TextField(label="Password", width=500, password=True, disabled=True)

    # File inputs and log area
    input_csv = ft.TextField(
        label="Datacite import CSV file", 
        disabled=True, 
        width=550
    )
    output_filename = ft.TextField(
        label="Output Filename",
        label_style=ft.TextStyle(color=ft.Colors.BLUE),  # Change label color to blue
        height=40,
        width=691, 
        hint_text="DataciteExport.csv",
        value="DataciteExport.csv"
    )
    output_directory = ft.TextField(
        label="Save Location",
        disabled=True,
        width=515
    )
    log_area = ft.ListView(expand=True, spacing=5, padding=10, auto_scroll=True)

    # Progress indicator
    progress = ft.ProgressBar(width=500, visible=False)

    # File pickers
    def pick_input_csv(e):
        if e.files:
            input_csv.value = e.files[0].path
            input_csv.update()

    def pick_save_location(e: FilePickerResultEvent):
        if e.path:
            output_directory.value = e.path
            output_directory.update()

    input_csv_picker = ft.FilePicker(on_result=pick_input_csv)
    save_location_picker = ft.FilePicker(
        on_result=pick_save_location
    )
    
    page.overlay.extend([input_csv_picker, save_location_picker])

    # Credentials file picker
    def pick_credentials_file(e: FilePickerResultEvent):
        if e.files:
            credentials_file_path = e.files[0].path
            try:
                with open(credentials_file_path, "r") as file:
                    credentials = json.load(file)
                    url_input.value = credentials.get("url", "")
                    doi_prefix_input.value = credentials.get("doiPrefix", "")
                    username_input.value = credentials.get("username", "")
                    password_input.value = credentials.get("password", "")
                    url_input.update()
                    doi_prefix_input.update()
                    username_input.update()
                    password_input.update()
                    log_area.controls.append(ft.Text("Credentials file loaded successfully!", selectable=True))
            except Exception as ex:
                log_area.controls.append(ft.Text(f"Error loading credentials file: {ex}", selectable=True))
            log_area.update()

    credentials_picker = ft.FilePicker(on_result=pick_credentials_file)
    page.overlay.append(credentials_picker)

    # Process CSV and submit DOIs
    def process_and_submit(e):
        if not input_csv.value:
            log_area.controls.append(ft.Text("Please select an input CSV file.", selectable=True))
            log_area.update()
            return

        if not output_filename.value or not output_directory.value:
            log_area.controls.append(ft.Text("Please specify both output filename and location.", selectable=True))
            log_area.update()
            return

        if not url_input.value or not doi_prefix_input.value or not username_input.value or not password_input.value:
            log_area.controls.append(ft.Text("Please upload a credentials file.", selectable=True))
            log_area.update()
            return

        progress.visible = True
        progress.update()

        try:
            # Combine directory and filename for output path
            output_path = os.path.join(output_directory.value, output_filename.value)
            log_dir = os.path.join(os.getcwd(), "log")
            os.makedirs(log_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file_path = os.path.join(log_dir, f"datacite_export_{timestamp}.csv")

            with open(input_csv.value, "r", newline="", encoding="utf-8") as file:
                header = [h.strip().lower() for h in file.readline().split(',')]
                reader = csv.DictReader(file, fieldnames=header)
                dois = []

                for row in reader:
                    creators = []
                    i = 1
                    while f"creator{i}" in row:
                        if row[f"creator{i}"]:
                            name_type = row.get(f"creator{i}_type", "").strip() or "Personal"
                            creators.append({
                                "name": row[f"creator{i}"].strip(),
                                "nameType": name_type,
                                "givenName": row.get(f"creator{i}_given", "").strip(),
                                "familyName": row.get(f"creator{i}_family", "").strip()
                            })
                        i += 1

                    dois.append({
                        "creators": creators,
                        "year": row["year"].strip(),
                        "url": row["source"].strip(),
                        "title": row["title"].strip(),
                        "type": row["type"].strip(),
                        "descriptions": [{
                            "description": row["description"].strip(),
                            "descriptionType": "Abstract"
                        }],
                        "publisher": row["publisher"].strip(),
                        "doi": ""
                    })

                results = []
                success_count = 0
                for doi in dois:
                    data = {
                        "data": {
                            "type": "dois",
                            "attributes": {
                                "event": "publish",
                                "prefix": doi_prefix_input.value,
                                "creators": doi["creators"],
                                "titles": [{"title": doi["title"]}],
                                "publisher": doi["publisher"],
                                "publicationYear": doi["year"],
                                "descriptions": doi["descriptions"],
                                "types": {
                                    "resourceTypeGeneral": "Text",
                                    "resourceType": doi["type"]
                                },
                                "schemaVersion": "http://datacite.org/schema/kernel-4",
                                "url": doi["url"]
                            }
                        }
                    }

                    response = requests.post(
                        url_input.value,
                        headers={"Content-Type": "application/vnd.api+json"},
                        data=json.dumps(data).encode("utf-8"),
                        auth=(username_input.value, password_input.value)
                    )

                    log_area.controls.append(ft.Text(f"\nSubmitting data to DataCite:\n{json.dumps(data, indent=4)}", selectable=True))
                    log_area.controls.append(ft.Text(f"Response for DOI generation: {response.status_code}", selectable=True))
                    log_area.controls.append(ft.Text(response.text, selectable=True))
                    log_area.update()

                    if response.status_code == 201:
                        success_count += 1
                        results.append({
                            "title": doi["title"],
                            "source": doi["url"],
                            "doi": f"https://doi.org/{response.json()['data']['id']}",
                            "status": 201,
                            "error_message": ""
                        })
                    else:
                        results.append({
                            "title": doi["title"],
                            "source": doi["url"],
                            "doi": None,
                            "status": response.status_code,
                            "error_message": response.json().get("errors", [{}])[0].get("title", "Unknown error")
                        })

                # Save results
                if page.web:
                    # For web, save to temporary file and trigger download
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.csv')
                    with open(temp_file.name, "w", newline="") as output_file:
                        writer = csv.DictWriter(output_file, fieldnames=["title", "source", "doi", "status", "error_message"])
                        writer.writeheader()
                        writer.writerows(results)
                    
                    with open(temp_file.name, 'rb') as f:
                        page.client_storage.set('download_data', f.read())
                        page.launch_url(f"/download/{os.path.basename(output_path)}")
                    
                    os.unlink(temp_file.name)
                else:
                    # For local app, save directly to specified location
                    with open(output_path, "w", newline="") as output_file:
                        writer = csv.DictWriter(output_file, fieldnames=["title", "source", "doi", "status", "error_message"])
                        writer.writeheader()
                        writer.writerows(results)

                    # Save a copy to the log directory
                    with open(log_file_path, "w", newline="") as log_file:
                        writer = csv.DictWriter(log_file, fieldnames=["title", "source", "doi", "status", "error_message"])
                        writer.writeheader()
                        writer.writerows(results)

                log_area.controls.append(ft.Text(f"\nDOIs processed. Results saved to {output_path}.", selectable=True))
                log_area.controls.append(ft.Text(f"Total DOIs successfully generated: {success_count}/{len(dois)}", selectable=True))
                log_area.update()

        except Exception as ex:
            log_area.controls.append(ft.Text(f"Error processing CSV: {ex}", selectable=True))
            log_area.update()

        progress.visible = False
        progress.update()

    # Navigation link to Page 1 (lower left)
    nav_link = ft.Row(
        [
            ft.TextButton("← DSPACE TO DATACITE CSV CONVERTER", on_click=lambda _: navigate_to_page2(page)),
            ft.TextButton("CSV MERGER FOR DSPACE IMPORT →", on_click=lambda _: navigate_to_page4(page)),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # Add components to the page
    page.add(
        header,
        description,
        spacer,
        ft.Column(
            [
                ft.ElevatedButton("Upload Credentials File", on_click=lambda _: credentials_picker.pick_files(allow_multiple=False, allowed_extensions=["json"])),
                url_input,
                doi_prefix_input,
                username_input,
                password_input,
            ],
            spacing=10,
        ),
        ft.Column(
            [
                ft.Row([
                    ft.ElevatedButton("Select Input CSV", on_click=lambda _: input_csv_picker.pick_files(allow_multiple=False, allowed_extensions=["csv"])),
                    input_csv
                ]),
                # Add spacing before output_filename
                ft.Container(height=15),
                output_filename,
                ft.Row([
                    ft.ElevatedButton(
                        "Choose Save Location",
                        on_click=lambda _: save_location_picker.get_directory_path()
                    ),
                    output_directory
                ]),
            ],
            spacing=10,
        ),
        ft.ElevatedButton("Process and Submit DOIs", on_click=process_and_submit),
        progress,
        log_area,
        nav_link
    )


#####################################################

# Page 4: CSV Merger
def page4(page: ft.Page):
    page.title = "CSV Merger for DSpace Import"

    # Add header and description
    header = ft.Text("CSV Merger for DSpace Import", size=24, weight="bold", color=ft.Colors.PINK_100)
    description = ft.Text(
         "Merge Datacite export CSV with DSpace Import CSV to update DOIs in DSpace. Final CSV will be named 'updated_<original_filename>'",
        size=14,
        color=ft.Colors.GREY_600,
    )
    spacer = ft.Container(height=10)

    auto_prefix_csv = ft.TextField(label="Datacite DOI export CSV file", disabled=True, width=500)
    dspace_csv = ft.TextField(label="DSpace CSV Import File", disabled=True, width=500)
    
    log = ft.ListView(expand=True, spacing=5, padding=10, auto_scroll=True)
    progress = ft.ProgressBar(width=500, visible=False)


    def pick_auto_prefix_file(e: FilePickerResultEvent):
        if e.files:
            auto_prefix_csv.value = e.files[0].path
            auto_prefix_csv.update()

    def pick_dspace_file(e: FilePickerResultEvent):
        if e.files:
            dspace_csv.value = e.files[0].path
            dspace_csv.update()


    def start_merging(e):
        if not dspace_csv.value or not auto_prefix_csv.value:
            log.controls.append(ft.Text("\nPlease select both input files.", selectable=True))
            log.update()
            return

        progress.visible = True
        progress.update()

        try:
            # Load Auto-prefix output CSV into a dictionary for easy lookup
            auto_prefix_data = {}
            with open(auto_prefix_csv.value, mode="r", encoding="utf-8") as auto_file:
                auto_reader = csv.DictReader(auto_file)
                for row in auto_reader:
                    auto_prefix_data[row["source"]] = row["doi"]

            # Define all possible `dc.identifier.uri` field names
            uri_fields = ["dc.identifier.uri[]", "dc.identifier.uri", "dc.identifier.uri[en]"]

            # Initialize counters
            dois_added = 0
            rows_skipped = 0
            total_auto_prefix_dois = len(auto_prefix_data)

            # Read the Dspace Import CSV and update the dc.identifier.uri fields
            updated_rows = []
            with open(dspace_csv.value, mode="r", encoding="utf-8") as dspace_file:
                dspace_reader = csv.DictReader(dspace_file)
                fieldnames = dspace_reader.fieldnames  # Retain original fieldnames

                for row in dspace_reader:
                    matched = False  # Track if any field matches the source
                    for uri_field in uri_fields:
                        if uri_field in row and row[uri_field].strip():  # Check if the field exists and has data
                            existing_uri = row[uri_field].strip()

                            # Skip if the URI already contains a DOI
                            if any(prefix in existing_uri for prefix in ["10.25316", "https://doi.org"]):
                                log.controls.append(ft.Text(f"Skipping row with existing DOI in field {uri_field}: {existing_uri}", selectable=True))
                                rows_skipped += 1
                                matched = True  # Mark as handled to avoid "No match" message
                                break

                            # Check for a match with the source
                            if existing_uri in auto_prefix_data:
                                log.controls.append(ft.Text(f"Match found for: {existing_uri} in field {uri_field}", selectable=True))
                                row[uri_field] += "||" + auto_prefix_data[existing_uri]
                                dois_added += 1
                                matched = True
                                break  # Stop further processing once a match is found

                    if not matched:
                        # Log a "No match" message only if no action was taken for any URI field
                        log.controls.append(ft.Text(f"No match for any field in row ID: {row.get('id', 'Unknown')}", selectable=True))

                    updated_rows.append(row)

            # Write the updated data back to a new CSV file
            from pathlib import Path

            dspace_path = Path(dspace_csv.value.strip())  # Remove extra spaces from the path
            output_csv = str(dspace_path.parent / f"updated_{dspace_path.name}")

            # Write the updated data back to a new CSV file
            with open(output_csv, mode="w", encoding="utf-8", newline="") as output_file:
                writer = csv.DictWriter(output_file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(updated_rows)

            # Sum it up!
            log.controls.append(ft.Text("\n--- Summary ---", selectable=True))
            log.controls.append(ft.Text(f"Total DOIs in Datacite Export CSV: {total_auto_prefix_dois}", selectable=True))
            log.controls.append(ft.Text(f"DOIs added: {dois_added}", selectable=True))
            log.controls.append(ft.Text(f"Rows skipped (DOI already present): {rows_skipped}", selectable=True))
            log.controls.append(ft.Text(f"Updated CSV saved as: {output_csv}", selectable=True))
            log.update()

        except Exception as ex:
            log.controls.append(ft.Text(f"Error processing CSV: {ex}", selectable=True))
            log.update()

        progress.visible = False
        progress.update()

    pick_dspace_file_picker = ft.FilePicker(on_result=pick_dspace_file)
    pick_auto_prefix_file_picker = ft.FilePicker(on_result=pick_auto_prefix_file)
    page.overlay.extend([pick_dspace_file_picker, pick_auto_prefix_file_picker])

    # Navigation link to Page 1 (lower left)
    nav_link = ft.Row(
        [
            ft.TextButton("← DATACITE BULK DOI CREATOR", on_click=lambda _: navigate_to_page3(page)),
            ft.TextButton("STATISTICS →", on_click=lambda _: navigate_to_page5(page)),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    page.add(
        header,
        description,
        spacer,
        auto_prefix_csv,
        ft.ElevatedButton("Select Datacite DOI Export CSV", on_click=lambda _: pick_auto_prefix_file_picker.pick_files(allow_multiple=False, allowed_extensions=["csv"])),
        dspace_csv,
        ft.ElevatedButton("Select DSpace Import CSV", on_click=lambda _: pick_dspace_file_picker.pick_files(allow_multiple=False, allowed_extensions=["csv"])),
        ft.ElevatedButton("Start Merging", on_click=start_merging),
        progress,
        log,
        nav_link
    )


#####################################################
# Page 5: Statistics

def page5(page: ft.Page):
    page.title = "Statistics"
    
    header = ft.Text("Statistics", size=24, weight="bold", color=ft.Colors.PINK_100)
    description = ft.Text(
        "Cumulative Total of DOIs Created by Prefix",
        size=14,
        color=ft.Colors.GREY_600,
    )
    spacer = ft.Container(height=10)
    
    stats_container = ft.ListView(
        expand=True,
        spacing=10,
        padding=20,
        height=400
    )
    
    def count_dois_by_prefix():
        prefix_counts = {}
        log_dir = os.path.join(os.getcwd(), "log")
        
        if not os.path.exists(log_dir):
            return prefix_counts
            
        try:
            for filename in os.listdir(log_dir):
                if filename.startswith("datacite_export_") and filename.endswith(".csv"):
                    with open(os.path.join(log_dir, filename), 'r', encoding='utf-8') as csvfile:
                        reader = csv.DictReader(csvfile)
                        for row in reader:
                            # Only count successfully created DOIs (status 201)
                            if row.get('status') == '201' and row.get('doi') and row['doi'].startswith('https://doi.org/'):
                                # Extract prefix from DOI
                                prefix = row['doi'].split('/')[3].split('.')[0] + '.' + row['doi'].split('/')[3].split('.')[1]
                                prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
        except Exception as e:
            stats_container.controls.append(
                ft.Text(f"Error reading file: {str(e)}", color=ft.colors.RED)
            )
            
        return prefix_counts

    def update_stats(e=None):
        # Clear existing statistics
        stats_container.controls.clear()
        
        # Add refresh button at the top
        stats_container.controls.append(
            ft.ElevatedButton(
                "Refresh Statistics",
                on_click=update_stats,
                icon=ft.Icons.REFRESH
            )
        )
        
        # Get DOI counts
        prefix_counts = count_dois_by_prefix()
        
        if not prefix_counts:
            stats_container.controls.append(
                ft.Text("No successful DOIs found in the log files.",
                       color=ft.Colors.GREY_600)
            )
        else:
            # Sort prefixes by count in descending order
            sorted_prefixes = sorted(prefix_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Create a card for each prefix
            for prefix, count in sorted_prefixes:
                stats_container.controls.append(
                    ft.Container(
                        content=ft.Row(
                            [
                                ft.Text(
                                    f"Prefix {prefix}",
                                    size=16,
                                    weight="bold",
                                    color=ft.Colors.GREY_900,
                                    width=200
                                ),
                                ft.Text(
                                    f"{count} DOIs",
                                    size=16,
                                    color=ft.Colors.GREY_900,
                                    weight="bold"
                                )
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                        ),
                        padding=10,
                        bgcolor=ft.Colors.PINK_100,
                        #border=ft.border.all(1, ft.Colors.GREY_300),
                        border_radius=5
                    )
                )
        
        stats_container.update()

    # Navigation link
    nav_link = ft.Row(
        [
            ft.TextButton("← CSV MERGER FOR DSPACE IMPORT", on_click=lambda _: navigate_to_page4(page)),
        ],
        alignment=ft.MainAxisAlignment.START,
    )

    # Add all components to the page first
    page.add(
        header,
        description,
        spacer,
        stats_container,  # Add the container to the page before updating it
        nav_link
    )
    
    # Now update the stats after the container is added to the page
    update_stats()


#############################################################


# Navigation functions
def navigate_to_page1(page: ft.Page):
    page.controls.clear()
    page1(page)
    page.update()

def navigate_to_page2(page: ft.Page):
    page.controls.clear()
    page2(page)
    page.update()

def navigate_to_page3(page: ft.Page):
    page.controls.clear()
    page3(page)
    page.update()

def navigate_to_page4(page: ft.Page):
    page.controls.clear()
    page4(page)
    page.update()

def navigate_to_page5(page: ft.Page):
    page.controls.clear()
    page5(page)
    page.update()

# Main app
def main(page: ft.Page):
    page.title = "DSpace and DataCite Tools"
    page1(page)  # Start with Page 1

ft.app(target=main)
