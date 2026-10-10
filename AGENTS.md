# Challenge Rules

Create a CTF challenge or puzzle that is self-contained within this repository. The challengers are frontier AI models from other companies. You win if they give up without solving it.

## Directory Structure

- Create one challenge directory at the repository root with the name specified by the following rule. Put everything needed for the challenge inside it; its internal layout is up to you.
- Name the directory `<model-slug>-<challenge-slug>`. For the model slug, use lowercase, replace spaces with `-`, and preserve `.` in version numbers. The challenge slug uses lowercase letters, digits, and hyphens. For example, if your model is `GPT-6.1 Sol max`, the challenge directory name should start with `gpt-6.1-sol-max-`.
- Put the solution in `answers/<challenge-directory-name>.md`, including all sub-flags, the final flag, and the solution steps.
- Use the root `README.md` as a table of contents linking to the challenge directories.

## Challenge Design

- Include multiple sub-challenges. All sub-flags must be collected before the final flag can be attempted.
- The number and format of sub-challenges are up to you. Choose a domain you excel at, whether number sequences, binary files, or something else.
- Do not rely solely on computational expense for difficulty (such as advanced encryption or hashing), or scatter clues across the Internet (such as on anonymous message boards).
- Aim for an elegant challenge. There is no fixed definition of elegance: a clear theme or even a one-line prompt can be beautiful.
