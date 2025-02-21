def save_as_markdown(output_file, data, gpt_summaries, title="Project Code Summary"):
    """Save extracted code summary and GPT summaries as a Markdown file."""
    with output_file.open("w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")

        for file, functions in data.items():
            if not functions or all("error" in func for func in functions):
                continue

            f.write(f"## {file}\n\n")
            f.write(
                f"**GPT Summary:** {gpt_summaries.get(file, 'No summary available.')}\n\n"
            )

            for func in functions:
                f.write(f"- **{func['type'].capitalize()}** `{func['name']}`\n")
                if func.get("args"):
                    f.write(f"  - Arguments: {', '.join(func['args'])}\n")
                f.write(f"  - Defined at line {func['lineno']}\n\n")
