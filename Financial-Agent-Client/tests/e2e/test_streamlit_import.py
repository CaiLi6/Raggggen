from __future__ import annotations


def test_streamlit_app_import_has_render_function() -> None:
    import ui.app as app

    assert callable(app.render_app)
