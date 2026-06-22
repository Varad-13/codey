# Usage

After successfully installing Codey, you can use it through the command line interface (CLI) in chat mode. Below are instructions on how to get started.

## Running Codey
To execute Codey, simply open your terminal and type:

```bash
codey
```

Once you run this command, you will enter a chat session where you can interact with the integrated AI. Feel free to ask questions or issue commands as you would in a normal conversation.

## Example Interaction
Here is an example of how a command might look in the chat:

```
User: What is the sum of 5 and 10?
Codey: The sum of 5 and 10 is 15.
```

Codey will automatically determine the nature of your request and respond accordingly. Enjoy exploring the capabilities of Codey!

## CLI Subcommands

In addition to chat mode, Codey supports a few non-interactive commands:

```bash
codey --version        # Print the installed version, e.g. `codey 0.4.0`.
codey -V               # Short form of --version.
codey update           # Check GitHub Releases for a newer version and install it.
```

### `codey update`

When you run `codey update`, Codey:

1. Calls `https://api.github.com/repos/Varad-13/codey/releases/latest`.
2. If a newer `tag_name` exists, finds the wheel asset named `codey-{version}-py3-none-any.whl`.
3. Downloads the wheel to a temp file.
4. Verifies its SHA256 against the asset's `digest` field (skipped only if the digest is missing).
5. Prompts you to confirm, then runs `pip install --upgrade --force-reinstall <wheel>`.

To suppress the startup update-check entirely (the network call made when `codey` launches in chat mode), set:

```bash
CODEY_NO_UPDATE_CHECK=1
```

`codey update` exits with code `0` when already up to date, and `1` only on genuine failures (network, hash mismatch, pip error, or user cancellation).