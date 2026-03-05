# Contributing to Google Ads API Agent

We welcome contributions! Here's how to get started.

## Priority Areas

1. **Optimization sub-agent actions** — The system prompt is written but needs API actions built
2. **Shopping & PMax sub-agent actions** — Same as above
3. **Test coverage** — Unit tests for the deploy package and action files
4. **Documentation** — Tutorials, guides, video walkthroughs

## Development Setup

```bash
# Clone
git clone https://github.com/itallstartedwithaidea/google-ads-api-agent.git
cd google-ads-api-agent

# Virtual environment
python -m venv venv
source venv/bin/activate

# Install with all extras
pip install -e ".[all]"

# Copy env template
cp .env.example .env
# Fill in your credentials

# Validate
python scripts/validate.py
```

## Submitting Changes

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Test with a Google Ads test account (never use production accounts for testing)
5. Commit with a clear message: `git commit -m "Add: optimization sub-agent bulk operations"`
6. Push and open a PR

## Code Style

- Python 3.10+ with type hints
- Follow existing patterns in `actions/` for new action files
- All actions must have a `run()` function as the entry point
- Use `logging` instead of `print()` for debug output

## Security

- **Never commit real API keys** — use `.env` and `.env.example`
- **Never log credentials** — mask sensitive values in debug output
- See [SECURITY.md](SECURITY.md) for the full security policy

## Action File Template

```python
"""
Action: My New Action
Description: What this action does
Credentials: Pattern B (4-key Google Ads)
"""

def run(action, customer_id=None, login_customer_id=None, **kwargs):
    """
    Entry point for the action.
    
    Args:
        action: The specific operation to perform
        customer_id: Google Ads customer ID
        login_customer_id: MCC account ID
    
    Returns:
        dict or str: Result of the operation
    """
    # Your implementation here
    pass
```
