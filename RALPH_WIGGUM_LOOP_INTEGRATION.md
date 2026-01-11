# Ralph-Wiggum Loop Integration for Eleven-Term

**Date**: 2026-01-XX  
**Status**: ✅ Implemented

## Overview

Integrated the Ralph-Wiggum loop concept from Anthropic's Claude-Code into Eleven-Term, enabling self-iterative AI loops for autonomous development workflows.

## What is Ralph-Wiggum Loop?

The Ralph-Wiggum loop is a mechanism that allows AI to work on a task iteratively until a completion criterion is met. The AI works on a task, attempts to exit, but gets re-prompted with the same input until it meets a completion criterion (e.g., outputting a specific phrase like "DONE" after passing tests).

## Implementation

### Files Created/Modified

1. **`loop_utils.py`** (NEW) - Core loop functionality
   - `LoopState` class for state management
   - `run_eleven_loop()` function for loop execution
   - State persistence to `~/.grok_terminal/loops/`
   - Logging to `~/.grok_terminal/loop_logs/`

2. **`main_helpers.py`** (MODIFIED)
   - Added `/eleven-loop` slash command handler
   - Added `/cancel-loop` slash command handler
   - Updated `handle_slash_commands()` to accept `args` parameter

3. **`grok_agent.py`** (MODIFIED)
   - Updated `handle_slash_commands()` call to pass `args` parameter

## Usage

### Interactive Mode

Start a loop in interactive mode:

```bash
eleven
```

Then use the slash command:

```
/eleven-loop Build a Python script for backups. Output DONE when tests pass. --completion-promise "DONE" --max-iterations 10
```

### Command Syntax

```
/eleven-loop <prompt> --completion-promise "<phrase>" [--max-iterations N]
```

**Parameters:**
- `<prompt>`: The task description (required)
- `--completion-promise "<phrase>"`: Exact string to detect completion (default: "DONE")
- `--max-iterations N`: Maximum number of iterations (default: 20)

### Cancelling a Loop

To cancel an active loop:

```
/cancel-loop
```

## Example Use Cases

### 1. Test-Driven Development

```bash
/eleven-loop Create a Python function to calculate fibonacci numbers. Write tests and output DONE when all tests pass. --completion-promise "DONE" --max-iterations 15
```

### 2. Code Refactoring

```bash
/eleven-loop Refactor the main.py file to use async/await patterns. Output COMPLETE when the code compiles and passes linting. --completion-promise "COMPLETE"
```

### 3. Bug Fixing

```bash
/eleven-loop Fix the memory leak in the cache module. Output FIXED when valgrind reports no leaks. --completion-promise "FIXED" --max-iterations 25
```

## How It Works

1. **Loop Initialization**: Creates a unique loop ID and initializes state
2. **Iteration Loop**:
   - Builds prompt with previous iterations' context
   - Calls NextEleven API with the prompt
   - Extracts and executes tools from the response
   - Checks for completion promise in the response
   - If found, exits with success
   - If not found and iterations < max, continues to next iteration
3. **State Persistence**: Saves state after each iteration to `~/.grok_terminal/loops/`
4. **Logging**: Logs each iteration to `~/.grok_terminal/loop_logs/`
5. **Completion**: Exits when completion promise is found or max iterations reached

## State Management

Loop state is saved to JSON files in `~/.grok_terminal/loops/`:
- Format: `loop_<timestamp>_<pid>.json`
- Contains: prompt, completion promise, iterations, context, files modified, git commits
- Completed loops are archived with `_completed.json` suffix

Logs are saved to `~/.grok_terminal/loop_logs/`:
- Format: `loop_<timestamp>_<pid>.txt`
- Contains: timestamped iteration logs with full responses and execution output

## Security Considerations

- Loops respect existing security mechanisms (command validation, permission prompts)
- Tool execution uses the same `execute_tool_safely()` function as normal mode
- Dangerous commands still require confirmation (unless `--dangerously-skip-permissions` is used)
- State files are stored in user's home directory with standard permissions

## Limitations

1. **API Costs**: Iterative calls can rack up API tokens - use `--max-iterations` to limit
2. **Infinite Loops**: Mitigated by `--max-iterations` cap (default: 20)
3. **State Management**: Files/Git state can get messy - consider using git stash before starting loops
4. **Context Summarization**: After 5+ iterations, only recent context (last 5 iterations) is included

## Future Enhancements

- [ ] Multi-condition exits (e.g., tests pass AND linting passes)
- [ ] Human-judgment tasks (pause for user input)
- [ ] Cost estimation preview before starting loops
- [ ] Git auto-commit per iteration option
- [ ] Rollback hooks for failed loops
- [ ] Loop resume functionality
- [ ] UI improvements with fzf for viewing iteration history

## Testing

Test the loop functionality:

```bash
# Simple test
eleven
/eleven-loop Generate a hello world script. Output DONE when done. --completion-promise "DONE" --max-iterations 5

# Cancel test
/cancel-loop
```

## Integration Notes

- Integrated with existing tool calling system
- Uses existing security and validation mechanisms
- Compatible with hooks system (PreToolUse/PostToolUse)
- Works with specialized agents via `--model` flag
- State persists across sessions (can be resumed in future)

## References

- Inspired by: https://github.com/anthropics/claude-code/tree/main/plugins/ralph-wiggum
- Eleven-Term repository: https://github.com/seanebones-lang/Eleven-Term
