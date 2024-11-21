from pathlib import Path
from typing import Any

from pydantic import TypeAdapter, ValidationError

from dandischema.models import Asset, Dandiset, PublishedAsset, PublishedDandiset

from .models import AssetValidationReport, DandisetValidationReport
from .tools import iter_direct_subdirs, pydantic_validate, write_reports

MANIFEST_DIR = Path("/Users/isaac/Downloads/mnt/backup/dandi/dandiset-manifests-s3cmd")
DANDISET_FILE_NAME = "dandiset.jsonld"  # File with dandiset metadata
ASSETS_FILE_NAME = "assets.jsonld"  # File with assets metadata
REPORTS_DIR = Path("../reports/validation")
REPORTS_FILE = REPORTS_DIR / "validation_reports.json"
ASSET_PYDANTIC_REPORTS_FILE = REPORTS_DIR / "asset_pydantic_validation_reports.json"

dandiset_validation_report_list_adapter = TypeAdapter(list[DandisetValidationReport])
ASSET_PYDANTIC_REPORT_LIST_ADAPTER = TypeAdapter(list[AssetValidationReport])


def main():
    def append_dandiset_validation_report() -> None:
        """
        Append a `DandisetValidationReport` object to `dandiset_validation_reports`
        if the current dandiset version directory contains a dandiset metadata file.
        """
        dandiset_metadata_file_path = version_dir / DANDISET_FILE_NAME

        # Return immediately if the dandiset metadata file does not exist in the current
        # dandiset version directory
        if not dandiset_metadata_file_path.is_file():
            return

        # Get the Pydantic model to validate against
        if dandiset_version == "draft":
            model = Dandiset
        else:
            model = PublishedDandiset

        dandiset_metadata = dandiset_metadata_file_path.read_text()
        pydantic_validation_errs = pydantic_validate(dandiset_metadata, model)
        # noinspection PyTypeChecker
        dandiset_validation_reports.append(
            DandisetValidationReport(
                dandiset_identifier=dandiset_identifier,
                dandiset_version=dandiset_version,
                pydantic_validation_errs=pydantic_validation_errs,
            )
        )

    def extend_asset_validation_reports() -> None:
        """
        Extend `asset_validation_reports` with `AssetValidationReport` objects if the
        current dandiset version directory contains an assets metadata file.
        """
        assets_metadata_file_path = version_dir / ASSETS_FILE_NAME

        # Return immediately if the assets metadata file does not exist in the current
        # dandiset version directory
        if not assets_metadata_file_path.is_file():
            return

        # Get the Pydantic model to validate against
        if dandiset_version == "draft":
            model = Asset
        else:
            model = PublishedAsset

        # JSON string read from the assets metadata file
        assets_metadata_json = assets_metadata_file_path.read_text()

        assets_metadata_type_adapter = TypeAdapter(list[dict[str, Any]])
        try:
            # Assets metadata as a list of dictionaries
            assets_metadata_python: list[dict[str, Any]] = (
                assets_metadata_type_adapter.validate_json(assets_metadata_json)
            )
        except ValidationError as e:
            msg = (
                f"The assets metadata file for "
                f"{dandiset_identifier}:{dandiset_version} is of unexpected format."
            )
            raise RuntimeError(msg) from e

        for asset_metadata in assets_metadata_python:
            asset_id = asset_metadata.get("id")
            asset_path = asset_metadata.get("path")
            pydantic_validation_errs = pydantic_validate(asset_metadata, model)
            asset_validation_reports.append(
                AssetValidationReport(
                    dandiset_identifier=dandiset_identifier,
                    dandiset_version=dandiset_version,
                    asset_id=asset_id,
                    asset_path=asset_path,
                    pydantic_validation_errs=pydantic_validation_errs,
                )
            )

    dandiset_validation_reports: list[DandisetValidationReport] = []
    asset_validation_reports: list[AssetValidationReport] = []
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

            append_dandiset_validation_report()
            extend_asset_validation_reports()

    # Ensure directory for reports exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    output_path = REPORTS_FILE
    output_path.write_bytes(
        dandiset_validation_report_list_adapter.dump_json(
            dandiset_validation_reports, indent=2
        )
    )

    # Write the asset Pydantic validation reports to a file
    write_reports(
        ASSET_PYDANTIC_REPORTS_FILE,
        asset_validation_reports,
        ASSET_PYDANTIC_REPORT_LIST_ADAPTER,
    )


if __name__ == "__main__":
    main()
