from pathlib import Path

from pydantic import TypeAdapter

from dandischema.models import Dandiset, PublishedDandiset

from .models import DandisetValidationReport
from .tools import iter_direct_subdirs, pydantic_validate

MANIFEST_DIR = Path("/Users/isaac/Downloads/mnt/backup/dandi/dandiset-manifests-s3cmd")
DANDISET_FILE_NAME = "dandiset.jsonld"  # File with dandiset metadata
REPORTS_DIR = Path("../reports/validation")
REPORTS_FILE = REPORTS_DIR / "validation_reports.json"

dandiset_validation_report_list_adapter = TypeAdapter(list[DandisetValidationReport])


def main():

    validation_reports: list[DandisetValidationReport] = []
    for n, dandiset_dir in enumerate(
        sorted(iter_direct_subdirs(MANIFEST_DIR), key=lambda p: p.name)
    ):
        # === In a dandiset directory ===
        dandiset_identifier = dandiset_dir.name
        print(f"{n}:{dandiset_identifier}: {dandiset_dir}")

        for version_dir in iter_direct_subdirs(dandiset_dir):
            # === In a dandiset version directory ===
            dandiset_version = version_dir.name
            print(f"\tdandiset_version: {dandiset_version}")

            # Get the Pydantic model to validate against
            if dandiset_version == "draft":
                model = Dandiset
            else:
                model = PublishedDandiset

            dandiset_metadata_file_path = version_dir / DANDISET_FILE_NAME

            if dandiset_metadata_file_path.is_file():
                dandiset_metadata = dandiset_metadata_file_path.read_text()
                pydantic_validation_errs = pydantic_validate(dandiset_metadata, model)
                # noinspection PyTypeChecker
                validation_reports.append(
                    DandisetValidationReport(
                        dandiset_identifier=dandiset_identifier,
                        dandiset_version=dandiset_version,
                        pydantic_validation_errs=pydantic_validation_errs,
                    )
                )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = REPORTS_FILE
    output_path.write_bytes(
        dandiset_validation_report_list_adapter.dump_json(validation_reports, indent=2)
    )


if __name__ == "__main__":
    main()
