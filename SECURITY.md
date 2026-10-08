# Security and operational safety

DocInvariant analyzes local text without sending it to an external service. It does not validate code execution safety, validate deployment operations, or approve security policies. Treat all detected or missed meaning changes as requiring human review.

Do not put live credentials, secrets, private user data, or proprietary manuals into public issues, test fixtures or pull requests. For a security-sensitive report, use GitHub's private vulnerability reporting feature if enabled, or contact the repository maintainer privately.

Do not run automatically rewritten safety-critical, destructive or access-control procedures without qualified approval. A scan with no findings is not assurance that the text is correct.
