from app import app, db
from models import Player
import csv
import os


def seed_players(csv_filename=None):
    """Seed the database with players from CSV file."""
    if csv_filename is None:
        csv_filename = "Fantasy_Football_2025_Draft.csv"  # Default filename

    with app.app_context():
        # Check if CSV file exists
        if not os.path.exists(csv_filename):
            print(f"Error: CSV file '{csv_filename}' not found!")
            print("Please make sure the CSV file is in the project root directory.")
            return

        count = 0
        skipped = 0

        with open(csv_filename, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                # Extract data from CSV (adjust column names to match your CSV)
                name = row["PLAYER NAME"].strip()
                pos_full = row["POS"].strip()
                nfl_team = row["TEAM"].strip()

                # Extract position (e.g., "WR1" -> "WR", "RB2" -> "RB")
                position = "".join([c for c in pos_full if c.isalpha()]).upper()

                # Only include QB, RB, WR, TE
                if position not in ["QB", "RB", "WR", "TE"]:
                    skipped += 1
                    continue

                # Check if player already exists
                existing = Player.query.filter_by(
                    name=name, position=position, nfl_team=nfl_team
                ).first()
                if existing:
                    skipped += 1
                    continue

                # Create new player
                player = Player(
                    name=name,
                    position=position,
                    nfl_team=nfl_team,
                    fantasy_points=None,
                    team_id=None,
                )
                db.session.add(player)
                count += 1

        db.session.commit()
        print(f"✅ Successfully seeded {count} players!")
        if skipped > 0:
            print(f"   (Skipped {skipped} duplicates or invalid positions)")


if __name__ == "__main__":
    seed_players()
