import json
# from config import METADATA_CONTEXT
from config import METADATA_STANDARD

def load_metadata_context():
    try:
        with open("schema.json", "r", encoding="utf-8") as file:
            schema_data = json.load(file)
            metadata_context = {}

            # Only load the selected metadata standard
            if METADATA_STANDARD == "dublin_core":
                metadata_context = schema_data.get("dublin_core", {})

            elif METADATA_STANDARD == "marc21":
                metadata_context = schema_data.get("marc21", {})

            return metadata_context
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading metadata context: {e}")
        return {}
    
# Load metadata schema into global context
METADATA_CONTEXT = load_metadata_context()

metadata_schema = {
    "name": "metadata_extraction",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False
    }
}

for field, details in METADATA_CONTEXT.items():
    if isinstance(details, dict):
        if details["type"] == "array":
            # ✅ Fix: Ensure arrays explicitly define "items"
            prop = {
                "type": "array",
                "items": {"type": "string"}
            }
        elif "properties" in details:
            # ✅ Fix: Remove `enum` if it's null
            prop = {
                "type": "object",
                "properties": {
                    sub_key: {
                        "type": sub_value["type"]
                    }
                    if "enum" not in sub_value or sub_value["enum"] is None  # ✅ Remove null enums
                    else {
                        "type": sub_value["type"],
                        "enum": sub_value["enum"]
                    }
                    for sub_key, sub_value in details["properties"].items()
                    if isinstance(sub_value, dict) and "type" in sub_value
                },
                "required": details.get("required", []),
                "additionalProperties": False
            }
        else:
            # ✅ Fix: Remove `enum: null`
            prop = {"type": details["type"]}
            if "enum" in details and details["enum"] is not None:
                prop["enum"] = details["enum"]

        metadata_schema["schema"]["properties"][field] = prop

        if "required" in details and details["required"]:
            metadata_schema["schema"]["required"].append(field)

print('OPENAI STRUCTURED OUTPUT:')
print(json.dumps(metadata_schema, indent=4, ensure_ascii=True))


