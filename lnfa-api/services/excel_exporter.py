import pandas as pd

def export_to_excel(data, filename="standings.xlsx"):
    file_path = f"./{filename}"

    with pd.ExcelWriter(file_path) as writer:

        pd.DataFrame(data.get("east", [])).to_excel(writer, sheet_name="East", index=False)
        pd.DataFrame(data.get("west", [])).to_excel(writer, sheet_name="West", index=False)
        pd.DataFrame(data.get("games", [])).to_excel(writer, sheet_name="Games", index=False)
        pd.DataFrame(data.get("players", [])).to_excel(writer, sheet_name="Players", index=False)

    return file_path