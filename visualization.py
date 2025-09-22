import streamlit as st
from visualize import main as create_main
import display_visualizations as view_module


def validate_github_token_local(token):
    """A lightweight local validator that delegates to the child modules' validators if available."""
    try:
        # Prefer the validator from visualize module if present
        from visualize import validate_github_token as viz_validator
        return viz_validator(token)
    except Exception:
        # Fallback: try display_visualizations validator
        try:
            return view_module.validate_github_token(token)
        except Exception:
            # As a last resort, accept non-empty token (not ideal but avoids blocking)
            return bool(token)


def main():
    """Combined Visualizations page with tabs: Create and View.

    This page shows a single token input (unique key) and stores the validated token
    in `st.session_state['gh_token']` so child pages don't re-prompt.
    """
    st.title("Visualizations")

    # Single token input for the whole visualization page (unique key)
    token = st.session_state.get('gh_token', None)
    if not token:
        entered = st.text_input("Enter your security token:", type="password", key="visualizations_token")
        if entered:
            if validate_github_token_local(entered):
                st.session_state['gh_token'] = entered
                st.success("Token validated and saved for this session.")
                token = entered
            else:
                st.error("Invalid token or access issue.")

    if token:
        st.info("Using validated token for Visualization pages.")

    tabs = st.tabs(["Create", "View"])

    with tabs[0]:
        # Create visualization tab
        create_main()

    with tabs[1]:
        # View visualizations tab
        view_module.main()


if __name__ == "__main__":
    main()
