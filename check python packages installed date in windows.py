import csv
import os
import site
from datetime import datetime

def get_site_packages():
    """Return all site-packages directories."""
    paths = []

    try:
        paths.extend(site.getsitepackages())
    except AttributeError:
        pass

    user_site = site.getusersitepackages()
    if user_site not in paths:
        paths.append(user_site)

    return paths


def get_packages():
    packages = []

    for site_path in get_site_packages():
        if not os.path.exists(site_path):
            continue

        for item in os.listdir(site_path):
            if item.endswith(".dist-info"):
                folder = os.path.join(site_path, item)

                try:
                    created = os.path.getctime(folder)
                    created_dt = datetime.fromtimestamp(created)

                    name_version = item[:-10]  # Remove ".dist-info"

                    # Split package name and version
                    parts = name_version.rsplit("-", 1)
                    if len(parts) == 2:
                        name, version = parts
                    else:
                        name = name_version
                        version = "Unknown"

                    packages.append({
                        "Package": name,
                        "Version": version,
                        "Installed Date": created_dt.strftime("%d-%m-%Y"),
                        "Installed Time": created_dt.strftime("%I:%M:%S %p"),
                        "Timestamp": created_dt,
                        "Location": folder
                    })

                except Exception:
                    pass

    packages.sort(key=lambda x: x["Timestamp"])
    return packages


def print_packages(packages):
    print("=" * 105)
    print(f"{'Package':30} {'Version':15} {'Installed Date':15} {'Time'}")
    print("=" * 105)

    for pkg in packages:
        print(
            f"{pkg['Package'][:30]:30} "
            f"{pkg['Version'][:15]:15} "
            f"{pkg['Installed Date']:15} "
            f"{pkg['Installed Time']}"
        )


def export_csv(packages):
    filename = "python_packages_install_dates.csv"

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        writer.writerow([
            "Package",
            "Version",
            "Installed Date",
            "Installed Time",
            "Location"
        ])

        for pkg in packages:
            writer.writerow([
                pkg["Package"],
                pkg["Version"],
                pkg["Installed Date"],
                pkg["Installed Time"],
                pkg["Location"]
            ])

    print(f"\nCSV exported successfully as '{filename}'")


def main():
    print("Python Executable:")
    print(os.path.realpath(os.sys.executable))
    print()

    packages = get_packages()

    if not packages:
        print("No pip-installed packages found.")
        return

    print_packages(packages)
    export_csv(packages)

    print(f"\nTotal Packages: {len(packages)}")


if __name__ == "__main__":
    main()
