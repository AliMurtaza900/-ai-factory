# GitHub Automation Layer

The Factory may prepare repository changes, but autonomous changes are bounded by
`GitHubAutomationPolicy`.

Default policy:

- changes use `factory/*` branches;
- force-push is disabled;
- deletion is disabled;
- changes should be reviewed through a pull request.

The connector implementation lives outside this package. This keeps credentials
and GitHub API access separate from generated-agent code.
