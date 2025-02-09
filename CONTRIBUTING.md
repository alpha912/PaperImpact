# Contributing to PaperImpact

Thank you for your interest in contributing to PaperImpact! We welcome contributions from everyone, whether it's bug fixes, new features, documentation improvements, or just thoughtful feedback.

## Ways to Contribute

*   **Report Bugs:** If you find a bug, please open an issue on GitHub, providing a clear description of the problem, steps to reproduce it, and your environment (operating system, Python version, etc.).
*   **Suggest Features:**  Have an idea for a new feature or improvement?  Open an issue on GitHub to discuss it.  We're open to suggestions!
*   **Fix Bugs:**  Look for open issues tagged as "bug" and submit a pull request with a fix.
*   **Implement Features:**  If you'd like to work on a new feature, please discuss it in an issue first to ensure it aligns with the project's goals.
*   **Improve Documentation:**  Help us make the documentation clearer, more complete, and easier to understand.  Submit pull requests with your changes.
*   **Write Tests:**  Help us improve the project's test coverage.

## Getting Started

1.  **Fork the Repository:** Click the "Fork" button on the top right of the [PaperImpact GitHub page](https://github.com/alpha912/PaperImpact) to create your own copy of the project.
2.  **Clone Your Fork:**
    ```bash
    git clone https://github.com/<your-username>/PaperImpact.git
    cd PaperImpact
    ```
3.  **Create a Branch:** Create a new branch for your work, using a descriptive name:
    ```bash
    git checkout -b feature/my-new-feature  # For a new feature
    git checkout -b bugfix/fix-some-bug     # For a bug fix
    ```
4.  **Set up a Development Environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Or venv\Scripts\activate on Windows
    pip install -r requirements.txt
    ```
5.  **Make Your Changes:**  Write your code, fix the bug, or improve the documentation.
6.  **Run Tests:**  Make sure your changes don't break existing functionality.  (Currently, there are no automated tests, but this is a planned future enhancement.  For now, manual testing is required.)
7.  **Commit Your Changes:**
    ```bash
    git add .
    git commit -m "Add a descriptive commit message"
    ```
    Use clear and concise commit messages.  Explain *what* you changed and *why*.
8.  **Push to Your Fork:**
    ```bash
    git push origin feature/my-new-feature
    ```
9.  **Create a Pull Request:** Go to the [PaperImpact GitHub page](https://github.com/alpha912/PaperImpact) and click "New Pull Request".  Select your fork and branch, and then create the pull request.  Provide a clear description of your changes in the pull request.

## Pull Request Guidelines

*   **Keep it Small:**  Smaller pull requests are easier to review and merge.  If you're working on a large feature, break it down into smaller, manageable parts.
*   **One Issue Per PR:**  Each pull request should address a single issue or feature.
*   **Follow the Code Style:**  The project uses the Black code formatter.  Run `black src/` before committing to ensure your code is formatted correctly.
*   **Write Clear Commit Messages:**  As mentioned above, use descriptive commit messages.
*   **Be Responsive:**  Respond to any feedback or questions on your pull request in a timely manner.
*   **Update the README:** If your changes affect how users interact with the project (e.g., new features, changes to command-line arguments), update the `README.md` file accordingly.

## Code Style

*   **Black:**  We use the [Black code formatter](https://github.com/psf/black) to ensure consistent code style.  Run `black src/` before committing.
*   **Docstrings:**  Use clear and concise docstrings to explain functions and classes.
*   **Comments:**  Add comments to explain complex logic or non-obvious code.
*   **Typing:** Use type hints where appropriate.

## Issue and Pull Request Labels

We use labels to categorize issues and pull requests:

*   **bug:**  Indicates a bug report.
*   **enhancement:**  Indicates a suggestion for a new feature or improvement.
*   **documentation:**  Indicates a need for documentation improvements.
*   **good first issue:**  Indicates an issue that is suitable for new contributors.
*   **help wanted:**  Indicates that we need help from the community to address an issue.
*   **question:** Indicates a question about the project.

Thank you for contributing to PaperImpact! 