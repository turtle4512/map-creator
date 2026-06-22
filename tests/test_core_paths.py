from guide_maps.core.paths import FONTS_DIR, PACKAGE_DIR, PROJECT_ROOT


def test_project_root_points_to_repository_root():
    assert (PROJECT_ROOT / "config.example.json").is_file()
    assert PACKAGE_DIR == PROJECT_ROOT / "guide_maps"
    assert FONTS_DIR == PACKAGE_DIR / "fonts"