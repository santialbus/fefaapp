import pandas as pd


def export_lnfa2_to_excel(data, filename="lnfa2.xlsx"):
    file_path = f"./{filename}"

    with pd.ExcelWriter(file_path) as writer:

        # 🧭 REGIONES
        for region, teams in data.get("regions", {}).items():
            pd.DataFrame(teams).to_excel(writer, sheet_name=region, index=False)

        # 📅 PARTIDOS
        pd.DataFrame(data.get("games", [])).to_excel(writer, sheet_name="Games", index=False)

        # 🧑 JUGADORES
        pd.DataFrame(data.get("players", [])).to_excel(writer, sheet_name="Players", index=False)

    return file_path