param(
    [Parameter(Mandatory=$false)]
    [string]$PRDFile = "PRD.md",

    [Parameter(Mandatory=$false)]
    [string]$ProgressFile = "progress.txt",

    [int]$MaxIterations = 10,
    [int]$SleepSeconds = 2,
    [int]$TimeoutMinutes = 30
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Ensure the PRD file exists so the agent has a starting point
if (-not (Test-Path $PRDFile)) {
    Write-Error "The PRD file '$PRDFile' was not found. Please create it or specify a valid path."
    exit 1
}

Write-Host "Starting Ralph - Max $MaxIterations iterations"
Write-Host "PRD File: $PRDFile"
Write-Host "Progress File: $ProgressFile"
Write-Host ""

for ($i = 1; $i -le $MaxIterations; $i++) {
    Write-Host "==========================================="
    Write-Host "  Iteration $i of $MaxIterations"
    Write-Host "==========================================="

    # The prompt now uses the variables passed into the script
    $prompt = @"
You are Ralph, an autonomous coding agent. Do exactly ONE task per iteration.

## Steps

1. Read $PRDFile and find the first task that is NOT complete (marked [ ]).
2. Read $ProgressFile - check the Learnings section first for patterns from previous iterations.
3. Implement that ONE task only.
4. Run tests/typecheck to verify it works.

## Critical: Only Complete If Tests Pass

- If tests PASS:
  - Update $PRDFile to mark the task complete (change [ ] to [x])
  - Commit your changes with message: feat: [task description]
  - Append what worked to $ProgressFile

- If tests FAIL:
  - Do NOT mark the task complete
  - Do NOT commit broken code
  - Append what went wrong to $ProgressFile (so next iteration can learn)

## Progress Notes Format

Append to $ProgressFile using this format:

## Iteration [N] - [Task Name]
- What was implemented
- Files changed
- Learnings for future iterations:
  - Patterns discovered
  - Gotchas encountered
  - Useful context
---

## Update AGENTS.md (If Applicable)

If you discover a reusable pattern that future work should know about:
- Check if AGENTS.md exists in the project root
- Add patterns like: 'This codebase uses X for Y' or 'Always do Z when changing W'
- Only add genuinely reusable knowledge, not task-specific details

## End Condition

After completing your task, check $PRDFile:
- If ALL tasks are [x], output exactly: <promise>COMPLETE</promise>
- If tasks remain [ ], just end your response with a minimal message (next iteration will continue)
"@

    $workDir = (Get-Location).Path
    $timeoutSec = $TimeoutMinutes * 60

    $job = Start-Job -ScriptBlock {
        param($promptText, $dir)
        Set-Location $dir
        & claude --dangerously-skip-permissions -p $promptText 2>&1 | Out-String
    } -ArgumentList $prompt, $workDir

    $null = $job | Wait-Job -Timeout $timeoutSec

    if ($job.State -eq 'Running') {
        Write-Warning "Iteration $i TIMED OUT after $TimeoutMinutes minutes - killing process"
        $job | Stop-Job
        $job | Remove-Job -Force

        # Log timeout to progress file using the variable
        $timeoutNote = "`n## Iteration $i - TIMEOUT`n- Task timed out after $TimeoutMinutes minutes`n- Process was killed`n---`n"
        Add-Content -Path $ProgressFile -Value $timeoutNote -ErrorAction SilentlyContinue

        Write-Host "Waiting $SleepSeconds seconds before retrying..." -ForegroundColor Yellow
        continue
    }

    try {
        $result = $job | Receive-Job 2>&1 | Out-String
        $job | Remove-Job -ErrorAction SilentlyContinue
    }
    catch {
        Write-Warning "Iteration $i failed with an error:"
        Write-Warning $_.Exception.Message
        $job | Remove-Job -Force -ErrorAction SilentlyContinue
        Write-Host "Waiting $SleepSeconds seconds before retrying..." -ForegroundColor Yellow
        continue
    }

    if (-not $result) {
        Write-Warning "Iteration $i returned empty output"
        Write-Host "Waiting $SleepSeconds seconds before retrying..." -ForegroundColor Yellow
        continue
    }

    Write-Host $result
    Write-Host ""

    if ($result -match "<promise>COMPLETE</promise>") {
        Write-Host "==========================================="
        Write-Host "  All tasks complete after $i iterations!"
        Write-Host "==========================================="
        exit 0
    }

    Start-Sleep -Seconds $SleepSeconds
}

Write-Host "==========================================="
Write-Host "  Reached max iterations ($MaxIterations)"
Write-Host "==========================================="
exit 1