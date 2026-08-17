# Per-repo fleet start config for suno-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'suno-mcp'
    BackendPort  = 10883
    FrontendPort = 10882
    HealthPath   = '/health'
    WebRoot      = 'D:\Dev\repos\suno-mcp\web_sota'
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'suno_mcp.server:app'
        SyncExtras    = @('dev')
        Env           = @{ WEB_PORT = '10883' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
