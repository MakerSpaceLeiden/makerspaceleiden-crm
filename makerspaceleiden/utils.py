from dynamic_filenames import FilePattern

upload_to_pattern = FilePattern(
    filename_pattern="{app_label:.25}/{model_name:.30}/{uuid:base32}{ext}"
)
