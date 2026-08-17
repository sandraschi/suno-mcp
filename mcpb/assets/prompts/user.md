# suno-mcp User Guide

## Overview

suno-mcp lets you generate music using Suno AI entirely through AI agent orchestration. You describe the music you want in natural language, and the server automates the entire workflow: opening a browser, authenticating, generating tracks, downloading them, and cleaning up. Because Suno has no public API, everything happens through a real Chromium browser under the hood. The server includes a full reconnaissance tool suite to handle Suno's frequently changing web interface.

## Getting Started

### First-Time Setup

The first time you use suno-mcp, you need to authenticate with Suno manually. This is a one-time setup that takes about 2 minutes:

1. Call `recon_ensure_authenticated_session()` -- this opens a visible Chromium browser window
2. In the browser window, manually log into your Suno account (you need a Suno account with credits or a subscription; a Premier subscription is recommended for Studio features)
3. Navigate to `suno.com/create` or `suno.com/library` to establish a valid session
4. The server detects the authenticated state and prompts you to save cookies
5. Call `recon_save_cookies("suno_session.json")` to persist the authentication for future headless use

After this initial setup, you can run completely automated sessions:

```
suno_open_browser(headless=True)
recon_load_cookies("suno_session.json")
suno_generate_track(prompt="Upbeat synthwave track", style="synthwave")
suno_get_status()
suno_download_track(track_id="...")
suno_close_browser()
```

### Quick Start

```
suno_open_browser(headless=True)
recon_load_cookies()
suno_generate_track(
    prompt="Upbeat electronic track with driving bass and synth melodies",
    style="electronic",
    duration="medium"
)
# Wait 30-60 seconds
suno_get_status()
# When complete
suno_download_track(track_id="track_abc123")
suno_close_browser()
```

## Music Generation

### Crafting Effective Prompts

The quality of generated music depends heavily on prompt quality. Suno AI responds best to detailed, evocative descriptions that give the model clear direction while leaving room for creativity.

**Structure your prompts with three elements:**
1. **Mood/genre**: The emotional quality and genre context
2. **Instruments/sound**: Specific instrumentation or production elements
3. **Structure**: Any structural cues like "builds up", "has a drop", "with a bridge"

Good examples:
- "Atmospheric ambient soundscape with evolving pad textures, gentle piano, and field recordings of rain"
- "Energetic drum and bass track with heavy sub-bass, rapid-fire breakbeats, and ethereal vocal samples"
- "Melodic synthwave with arpeggiated Juno-style chords, gated reverb snare, and a walking bassline"
- "Lo-fi hip hop with vinyl crackle, warm Rhodes piano chords, and a relaxed boom-bap drum beat"

Poor examples:
- "Make a song" -- too vague, no direction
- "Something nice" -- no musical content to work with
- "Music" -- single word, no useful information

### Style Selection

The `style` parameter sets the musical genre and influences production aesthetic. The style parameter acts as a high-level filter that couples with the prompt text. Common styles include:
- **synthwave**: Retro 80s electronic with arpeggiated synths, gated reverb, and analog warmth
- **pop**: Modern pop production with clear verse-chorus structure and polished mix
- **rock**: Guitar-driven with live drums, bass, and often distorted guitars
- **lo-fi**: Relaxed, imperfect production with vinyl crackle, tape hiss, and warm saturation
- **jazz**: Acoustic instruments with swing feel, improvisation, and complex harmony
- **classical**: Orchestral or chamber music with formal structure and notation
- **electronic**: Broad category from ambient textures to driving techno beats
- **hip-hop**: Beat-driven production with rhythmic vocals and prominent bass
- **ambient**: Atmospheric, minimal, textural -- often lacks traditional rhythm
- **industrial**: Harsh electronic with metallic percussion and distorted synths
- **funk**: Syncopated basslines, brass stabs, tight drumming
- **r-and-b**: Smooth vocals with contemporary production, often hip-hop influenced
- **folk**: Acoustic instrumentation with storytelling vocals
- **metal**: Heavy distorted guitars, fast drums, aggressive vocals
- **blues**: 12-bar structure, expressive guitar, soulful vocals
- **country**: Acoustic and steel guitar, narrative lyrics
- **reggae**: Offbeat rhythm, heavy bass, laid-back feel

### Lyrics

To include sung or rapped lyrics, pass them in the `lyrics` parameter. The lyrics should be poetic and fit the musical style. Suno AI sings or raps the lyrics over the generated instrumental. Lyrics work best when they match the style: poetic verses for folk, rhythmic bars for hip-hop, catchy hooks for pop. For instrumental-only tracks, omit the lyrics parameter and focus the prompt on instrumental elements.

### Duration

The `duration` parameter controls approximate track length. Longer tracks take more generation time and credits:
- "auto": Let the model decide (usually 30-60 seconds). Best when you are not sure what length works.
- "short": Approximately 30 seconds. Good for previews, jingles, or sound design elements.
- "medium": Approximately 60 seconds. Good for most music applications -- long enough for a verse-chorus structure.
- "long": Approximately 2 minutes. Good for full songs, background music, or extended compositions.

### Track Management

After generation starts, Suno displays the track in its library. Track IDs are visible in the Suno URL when viewing a specific track (e.g., `suno.com/track/abc123`). Track IDs are alphanumeric strings. Downloads include the main audio file (MP3 or WAV format) and optionally stems (individual instrument tracks) if Suno provides them and your subscription supports it.

## Batch Generation

For generating multiple tracks efficiently:
1. Open browser and authenticate once (suno_open_browser + recon_load_cookies)
2. Submit multiple `suno_generate_track` calls sequentially -- Suno limits concurrent generations
3. Track IDs are returned immediately for each call
4. Poll `suno_get_status()` for each track independently
5. Download completed tracks as they become ready
6. Close the browser when all tracks are downloaded

## Agentic Workflow

The `agentic_suno_workflow` tool lets you express high-level music goals in natural language:

```
agentic_suno_workflow(
    workflow_prompt="Generate a synthwave track, wait for it to complete, download it, and close the browser",
    available_tools=["suno_open_browser", "suno_login", "suno_generate_track",
                     "suno_get_status", "suno_download_track", "suno_close_browser"]
)
```

The LLM (via sampling) breaks the goal into steps, calls the appropriate tools, checks intermediate results, and iterates until the goal is achieved.

**When to use agentic vs manual:**
- Use agentic for: one-shot goals, experimentation, quick results when you are not sure of the exact workflow
- Use manual for: precise control over prompts and styles, debugging automation failures, inspecting intermediate state

## Reconnaissance Workflow

When Suno updates its web interface, automation scripts may break. The recon suite is designed to detect and adapt to UI changes.

### Detecting UI Drift

Run `recon_periodic_dom_snapshots()` regularly (e.g., weekly) to build a history of UI changes. If the snapshots show significant structural changes, it is time to update automation selectors.

### Interactive Element Discovery

When selectors fail, run `recon_find_elements()` to map all interactive elements on the current page. The output prioritizes the most stable selectors. Update your automation scripts based on the findings.

### Session Health Monitoring

Use `suno_get_status()` during automation runs to verify browser health. Key status indicators:
- `browser_open`: false if the browser crashed or was closed
- `page_ready`: false if the page is still loading or has errors
- `in_studio`: true when on a Studio page
- `current_url`: shows which Suno page the browser is on

If `browser_open` is false, call `suno_open_browser()` again. If `page_ready` is false, wait and retry.

## Output Files

All server output is organized under the working directory:
- DOM captures: `recon_output/studio_dom_*.html`
- Analysis JSON: `recon_output/studio_analysis_*.json`
- Element maps: `recon_output/interactive_elements_*.json`
- Cookies: `recon_output/suno_cookies.json` (or custom name)
- Screenshots: `recon_output/studio_screenshot_*.png`
- Track downloads: `downloads/` or custom path

## Example Workflows

### Workflow: Generate and Download a Complete Track
1. `suno_open_browser(headless=True)` -- start hidden browser
2. `recon_load_cookies()` -- restore authentication
3. `suno_get_status()` -- verify session is valid
4. `suno_generate_track(prompt="Upbeat synthwave", style="synthwave", duration="medium")`
5. `suno_get_status()` -- poll every 10s until track is ready
6. `suno_download_track(track_id="abc123")` -- save audio files
7. `suno_close_browser()` -- cleanup

### Workflow: Batch Generate Multiple Track Variations
1. `suno_open_browser(headless=True)` + `recon_load_cookies()`
2. Generate track 1: `suno_generate_track(prompt="Energetic rock", style="rock")` -> track_id_1
3. Wait 30s (Suno cooldown)
4. Generate track 2: `suno_generate_track(prompt="Mellow acoustic", style="folk")` -> track_id_2
5. Poll both: `suno_get_status()` for each
6. Download completed tracks: `suno_download_track(track_id_1)`, `suno_download_track(track_id_2)`
7. `suno_close_browser()`

### Workflow: Studio Reconnaissance for Automation Development
1. `recon_start_session(headless=False)` -- visible browser
2. Manually login to Suno Premier
3. Navigate to Studio
4. `recon_capture_dom()` -- capture full Studio DOM structure
5. `recon_find_elements()` -- map all interactive controls
6. `recon_save_cookies("premier_cookies.json")` -- save for headless use
7. `recon_screenshot("studio_overview.png")` -- visual reference
8. `recon_close_session()`

### Workflow: Agentic Music Creation
1. `agentic_suno_workflow(workflow_prompt="Create a lo-fi beat, wait for it, download it to the music folder", available_tools=["suno_open_browser", "suno_generate_track", "suno_get_status", "suno_download_track", "suno_close_browser"])`
2. The agentic workflow handles: opening browser, generating, waiting, downloading, closing
3. No manual polling needed -- the LLM checks results and decides next steps

### Workflow: UI Drift Detection
1. Schedule: `recon_periodic_dom_snapshots(interval_seconds=3600, iterations=24, prefix="daily_drift", include_element_map=true)`
2. After 24 hours, review captured DOM snapshots
3. Compare with baseline from when selectors last worked
4. If structures changed: update automation selectors based on new snapshots
5. Archive old baseline after confirming new selectors work

## Prompt Refinement Patterns

When a generated track does not meet expectations, refine the prompt using these patterns:

### Pattern: Add Specificity
Bad: "Make a cool song"
Good: "Electronic track with a driving four-on-the-floor kick drum, syncopated bassline, and atmospheric synth pads"

### Pattern: Reference Artist or Era
Bad: "Some music"
Good: "Synthwave track in the style of 1980s John Carpenter film scores with arpeggiated sequencers"

### Pattern: Specify Structure
Bad: "A song"
Good: "A track that starts with a minimal beat, builds up with layers of synths, has a drop into a driving bassline, and fades out with ambient pads"

### Pattern: Include Production Details
Bad: "Pop music"
Good: "Modern pop production with punchy compressed drums, layered vocal harmonies, wide stereo synths, and a polished master"

## Troubleshooting Common Generation Issues

### "Generation failed" with no details
- Check `suno_get_status()` for browser state
- The page may have timed out or crashed -- close and reopen
- Suno may be down or under maintenance -- try the Suno web interface directly

### Track generated but sounds wrong
- The prompt may have been too vague or contradictory
- Try again with a simpler, more focused prompt
- Change the style parameter to something more specific

### Download fails with "file not found"
- The track may not have finished generating -- wait longer
- The track_id may be incorrect -- check the Suno library URL
- Suno may have deleted the track (if content policy violation)

### "Stems not available"
- Stem support depends on the generation model plan
- Not all Suno subscriptions include stem download
- Set `include_stems=False` if you consistently get this error

## Understanding Suno Credits and Limits

- Suno accounts have credits that are consumed per generation
- Generation time includes compute time on Suno's servers
- Free tiers have daily limits (typically 5-10 generations per day)
- Premier subscriptions have higher limits and faster generation
- Credit usage: short tracks use fewer credits, long tracks use more
- Failed generations typically do not consume credits (but check your Suno account)
- The server does not track credit usage -- monitor via your Suno account dashboard

## Comparing suno-mcp with Other Approaches

suno-mcp is unique in that it automates a web interface rather than using an API. This has implications:
- No API keys needed for Suno (authentication is through the browser)
- Works with any Suno subscription tier (free or paid)
- Fragile to UI changes (no stable contract with Suno)
- Slower than API-based approaches (browser overhead)
- Supports all Suno features exposed through the web UI

Alternatives for AI music generation MCP include using API-based services like ElevenLabs or Google's MusicLM, but these have different capabilities and limitations compared to Suno.

## Future Updates and Compatibility

Suno AI's web interface changes frequently, which may affect suno-mcp's automation. Key considerations:

**Suno UI updates**: The Suno team updates the web interface regularly. When selectors break, run `recon_capture_dom()` and `recon_find_elements()` to discover the new structure.

**Suno API or policy changes**: If Suno introduces rate limits, captchas, or blocks automated access, the server may stop working until the automation approach is updated.

**Server version updates**: Update suno-mcp regularly to get the latest selector mappings and fixes for Suno UI changes. Check the repo for new releases.

**Cookie expiration**: Suno session cookies expire periodically. When automation stops working, check `suno_get_status()` for authentication state. If expired, re-authenticate manually and save new cookies.

## Safety and Best Practices

When using suno-mcp for automated music generation, follow these best practices:

**Credit management**: Monitor your Suno account credit balance regularly. Each generation consumes credits. Set up alerts if available through your subscription tier.

**Content policy compliance**: Ensure your prompts and lyrics comply with Suno's content policy. Do not generate music that infringes copyright, contains offensive content, or violates terms of service.

**File organization**: Keep generated tracks organized by project and date. Use meaningful download paths and rename files after download for clarity.

**Session cleanup**: Always call `suno_close_browser()` at the end of a session. Abandoned browser sessions consume memory and may leave temporary files.

**Security**: Cookie files grant full Suno account access. Store them in a secure location, restrict access to authorized users, and rotate cookies periodically.

## Understanding Server-Side vs Client-Side Sampling

suno-mcp supports two sampling modes that affect how `agentic_suno_workflow` operates:

**Server-side sampling (SUNO_SAMPLING_USE_CLIENT_LLM=0, default)**:
- The server connects to its own LLM at SUNO_SAMPLING_BASE_URL (default Ollama at http://127.0.0.1:11434/v1)
- This works in any MCP client, even those without sampling support
- The LLM model is configured via SUNO_SAMPLING_MODEL env var
- Best for: local setups with Ollama, compatibility across all clients

**Client-side sampling (SUNO_SAMPLING_USE_CLIENT_LLM=1)**:
- The server delegates sampling to the connected MCP client (Claude Desktop, Cursor)
- Uses the client's native LLM capabilities (typically higher quality)
- Required for SEP-1577 sampling-with-tools mode where the LLM calls tools as part of sampling
- Best for: Claude Desktop (supports native sampling), higher quality LLM access

### Switching Modes
- To switch between modes, set the env var and restart the server
- The agentic workflow tool works in both modes but behavior may differ
- In client mode, the LLM has access to all registered server tools and can chain them together

## Understanding Generation Quality Factors

Several factors affect the quality of AI-generated music from Suno:

**Prompt specificity**: Detailed, multi-sentence prompts produce more coherent tracks than short generic prompts. Include mood, instruments, tempo, and structure cues.

**Style selection**: Choosing the correct style parameter is critical. A prompt about "driving bass" works better with "electronic" or "hip-hop" than with "classical" or "folk".

**Lyrics quality**: If providing lyrics, well-structured verses with consistent meter produce better results. Avoid random phrases or prose-style lyrics.

**Duration**: Longer tracks (medium/long) allow the model more time to develop musical ideas but may introduce structural drift towards the end.

**Generation variance**: The same prompt can produce very different tracks across multiple generations. Generate 3-5 variants of a good prompt and select the best one.

**Seed consistency**: Suno does not expose a seed parameter, so there is no way to reproduce specific generations exactly.

## Suno AI Studio Features

Suno Studio (Premier subscription required) provides advanced music editing capabilities beyond basic generation:

**Timeline editing**: Adjust the arrangement of generated sections, loop segments, and extend or trim the track duration.

**Stem separation**: Isolate vocals, drums, bass, and other instruments for individual mixing and processing.

**Parameter automation**: Adjust volume, pan, and effects over time for dynamic mixes.

**Export options**: Export individual stems as WAV files or the full mix as MP3/WAV.

The recon tools in suno-mcp can discover Studio UI elements for automation development. However, Studio interaction beyond basic generation is not currently automated. Use the visible browser workflow for Studio operations.

## Understanding Suno AI Generation Limits

Suno AI has several implicit limits that affect the server's operation:

**Generation queue**: Suno allows one generation at a time by default. If you submit multiple tracks rapidly, they may be queued or the second one may fail. Always wait for the first track to complete before starting the next.

**Daily generation limit**: Depends on your Suno subscription tier. Free tiers typically allow 5-10 generations per day. Premier subscribers get significantly more. The server does not track this -- check your Suno account dashboard.

**Content policy**: Suno may reject generations that violate their content policy (explicit lyrics, copyrighted prompts, offensive content). If a generation fails immediately without progress, the prompt may be blocked. Review Suno's content policy and adjust your prompts.

**Prompt length**: Suno has a maximum prompt length (typically 500-1000 characters). Very long prompts are truncated. Keep prompts under 500 characters for reliable generation.

**Audio quality**: Suno generates audio at variable quality depending on the model and subscription. Free tiers may have lower quality (lower sample rate, more artifacts). Premier subscribers get the highest quality output.

## File Management

The server generates several types of output files that need periodic management:

### Downloaded Tracks
- Tracks are saved to `downloads/` by default (or custom path)
- File sizes: 3-15 MB per track (MP3), 30-100 MB per track (WAV with stems)
- Organization: files are named by Suno's convention (usually the prompt or track ID)
- Cleanup: delete files from `downloads/` after use if space is a concern

### Recon Output Files
- DOM snapshots: 100KB-2MB each (HTML + JSON)
- Screenshots: 500KB-3MB each (PNG)
- Element maps: 50-200KB each
- Periodic snapshots can accumulate quickly -- delete old ones periodically
- Retention: 30-60 days recommended unless needed for UI drift analysis

### Cookie Files
- Size: 1-5KB
- Security: These grant full account access. Store in a secure location.
- Cleanup: Only keep cookies for active accounts. Delete old ones.
- Never commit to git (add recon_output/ to .gitignore)

## Audio Output Quality

Generated tracks from Suno AI are typically 44.1kHz or 48kHz stereo MP3/WAV. The download format depends on Suno's current output settings:
- Standard download: MP3 (128-320 kbps, variable)
- Stem download: individual WAV files per instrument (when available)
- Extended range: some tracks may have limited frequency response (typically 20Hz-16kHz)

### Recommended Post-Processing
After downloading, consider:
- **Normalization**: Use ffmpeg or Audacity to normalize loudness to -14 LUFS (streaming standard)
- **Trimming**: Remove silence at the beginning and end of the track
- **Fade in/out**: Apply short fades to avoid clicks
- **Format conversion**: Convert MP3 to WAV or FLAC for higher quality editing

## Integration with Other MCP Tools

suno-mcp can be combined with other fleet MCP tools:

- **google-ai-mcp**: Use Google-ai image generation to create album art for generated tracks
- **reaper-mcp**: Import generated tracks into Reaper for arrangement and mixing
- **godot-mcp**: Use generated music as background audio for game development
- **email-mcp**: Share generated tracks by emailing download links
- **discord-mcp**: Announce new track releases in a Discord channel

Example cross-tool workflow:
1. `suno_generate_track(prompt="Upbeat game theme", style="electronic")`
2. `suno_download_track(track_id="...")`
3. Import into game project via godot-mcp
4. Announce in Discord: "New game music track generated!"

## Session Management Best Practices

### Cookie Lifecycle
- Save cookies immediately after a successful manual login
- Cookies typically expire after 7-30 days (Suno policy may vary)
- If automation stops working, cookies may have expired -- run manual login again
- Store separate cookie files for different accounts or subscription tiers
- Never commit cookie files to version control

### Concurrent Session Handling
- The server supports one active browser session at a time
- Before starting a new session, ensure the old one is closed with `suno_close_browser()`
- Use `suno_get_status()` to verify the browser state before operations
- If you need to switch accounts: close browser, change cookies, reopen browser

### Error Recovery Flow
When an operation fails:
1. `suno_get_status()` -- check if browser is still alive
2. If browser is dead: `suno_open_browser()` + `recon_load_cookies()`
3. If browser is alive but not authenticated: `recon_load_cookies()` or manual login
4. Retry the failed operation
5. If persistent failure: close and reopen browser entirely

## Understanding the Agentic Workflow

The `agentic_suno_workflow` tool uses the FastMCP SEP-1577 sampling protocol to plan and execute multi-step music generation tasks. Here is how it works internally:

1. The LLM receives the `workflow_prompt` as a user message and the `available_tools` as a tool list.
2. The LLM plans a sequence of steps (e.g., "First open the browser, then generate a track, then wait for it").
3. For each step, the LLM calls one of the available tools with specific parameters.
4. The server executes the tool and returns the result to the LLM.
5. The LLM examines the result and decides the next step.
6. This loop continues until the goal is achieved or `max_iterations` is reached.
7. The server returns the final output from the LLM.

The workflow is most effective when:
- The `workflow_prompt` clearly states the goal and any constraints
- The `available_tools` list includes all tools that might be needed
- `max_iterations` is set high enough for complex workflows (5-10 for multi-track generation)
- The LLM used for sampling has good reasoning capabilities (Claude or GPT-4 class)

## Comparison with Other Music Generation Approaches

**vs. Suno Web Interface**: suno-mcp automates what you would do manually at suno.com. The advantage is scriptability, batch generation, and integration with other MCP tools. The disadvantage is fragility (UI changes) and no access to features not exposed via the web UI.

**vs. Suno API (if it existed)**: If Suno had an official API, it would be faster and more reliable than browser automation. suno-mcp exists because Suno does not provide a public API. The recon tools exist to handle the brittleness of browser automation.

**vs. Other AI music generators**: Suno is one of several AI music platforms. Alternatives include Udio, Riffusion, MusicGen, and Stable Audio. Each has its own strengths -- Suno excels at prompt fidelity and style variety. suno-mcp only supports Suno.

**vs. Traditional music production**: AI-generated music from Suno is not a replacement for professional music production. It is best for quick sketches, background music, inspiration, and content where production quality is secondary.

## Configuration

Environment variables control the server's sampling behavior:
- `SUNO_SAMPLING_BASE_URL`: LLM endpoint for server-side sampling (default `http://127.0.0.1:11434/v1`)
- `SUNO_SAMPLING_MODEL`: Model name for server-side sampling
- `SUNO_SAMPLING_USE_CLIENT_LLM`: Set to "1" to use the host MCP client's LLM for sampling

No API keys are needed for Suno itself -- authentication is handled through browser cookies. LLM sampling may need an Ollama instance or API keys depending on configuration.

## Safety Notes

- Suno accounts are tied to paid subscriptions or credit packages. Each generation consumes credits. Monitor your usage to avoid surprise charges.
- Cookie files grant full account access. Store them securely and never commit them to version control. The `recon_output/` directory is gitignored by convention.
- Browser automation with `headless=False` opens visible browser windows. Do not share screenshots that show login pages with visible credentials.
- Suno may rate-limit or block automated access patterns. Use reasonable intervals between operations (at least 5-10 seconds).
- The server only interacts with `suno.com` and its subdomains. It does not access any other websites or services.

## Advanced Prompt Crafting

### Musical Structure Keywords

Include these keywords in your prompt to suggest musical structure:
- "intro", "verse", "chorus", "bridge", "outro" -- song section structure
- "build up", "drop", "climax" -- dynamic arc
- "breakdown", "interlude" -- quieter sections
- "solo" -- instrumental feature
- "fade in", "fade out" -- beginning/end transitions

### Mood and Texture Keywords

- "atmospheric", "ethereal", "dreamy", "spacey" -- ambient textures
- "aggressive", "intense", "driving", "powerful" -- high energy
- "mellow", "relaxed", "chill", "smooth" -- low energy
- "dark", "brooding", "ominous", "tense" -- negative emotional quality
- "uplifting", "joyful", "bright", "hopeful" -- positive emotional quality
- "nostalgic", "melancholic", "bittersweet" -- reflective emotional quality

### Production Keywords

- "lo-fi", "vintage", "warm", "analog" -- retro production
- "clean", "polished", "modern", "pristine" -- contemporary production
- "glitchy", "distorted", "noisy", "raw" -- experimental production
- "minimal", "sparse", "intimate" -- stripped-down arrangement
- "grand", "epic", "cinematic", "large" -- expansive arrangement

## Working with Generated Tracks

### Evaluating Quality

When listening to generated tracks, consider:
- **Structure**: Does the track have a clear beginning, middle, and end? Does it develop over time or stay static?
- **Cohesion**: Do the instruments work together? Is the style consistent throughout?
- **Novelty**: Is the track interesting beyond the first listen? Does it have unexpected elements?
- **Fidelity**: Is the audio quality acceptable? Are there artifacts or glitches?

### Iterating on Prompts

If a generation does not match your expectations, refine the prompt:
1. Add more specific instrument references: "with flanger on the pads" instead of "with effects"
2. Adjust the style parameter: "synthwave" vs "electronic" make big differences
3. Specify tempo or energy level: "slow and mellow" vs "fast and energetic"
4. Reference specific artists or songs as touchstones: "in the style of Tycho"

### Organizing Downloads

The download system saves files to the specified `download_path`. For project organization:
- Use separate folders per project: `downloads/my-album/track1/`
- Use `include_stems=True` to get individual instrument files
- Track naming conventions: Suno generates filenames; rename after download for clarity

## Using Multiple Suno Accounts

If you have multiple Suno accounts (e.g., personal and team), save separate cookie files and load the appropriate one:
```
# Save account A cookies
recon_save_cookies("account_a.json")
# Later, switch to account B
recon_load_cookies("account_b.json")
```

Each account has its own credit balance and generation history. Cookie files are interchangeable as long as they contain valid, non-expired sessions.

## Prompt Gallery

### Electronic Music
- "Deep house with warm bassline, soft pads, and a steady four-on-the-four kick"
- "Ambient techno with minimal percussion and evolving synth textures"
- "Acid house with squelching 303 bassline and 909 drums"
- "Progressive trance with build-ups, melodic leads, and euphoric breakdowns"

### Hip-Hop and R&B
- "Boom-bap hip-hop with dusty sampled drums, jazz loop, and deep bass"
- "Trap beat with heavy 808s, rolling hi-hats, and dark synth melody"
- "Neo-soul with smooth Rhodes piano, lazy drums, and warm bass"

### Rock and Alternative
- "Indie rock with jangly guitars, driving drums, and catchy vocal melody"
- "Post-rock with crescendos, delay-heavy guitars, and orchestral swells"
- "Psychedelic rock with wah-wah guitar, organ, and reverb-heavy production"

### World and Fusion
- "Afrobeat with polyrhythmic percussion, horn section, and funky guitar"
- "Bossa nova with acoustic guitar, soft percussion, and Portuguese-style vocals"
- "Indian fusion with sitar, tabla, and electronic production"

### Ambient and Experimental
- "Dark ambient with drone textures, field recordings, and subtle glitch effects"
- "Generative ambient with slowly evolving pads and gentle modulation"
- "Soundscape with water sounds, distant bells, and atmospheric strings"

## Troubleshooting

**"Browser not open"**: Call `suno_open_browser()` first before any other operation. The browser must be initialized before login or generation.

**"Not authenticated"**: Your session is not valid. Call `recon_ensure_authenticated_session()` for the guided manual login flow, or load saved cookies with `recon_load_cookies()`.

**Generation stuck or hanging**: Call `suno_get_status()` to check browser state. If the browser appears unresponsive, close it with `suno_close_browser()`, re-open with `suno_open_browser()`, re-authenticate, and retry generation.

**Login fails**: Suno uses Clerk authentication which is updated frequently by Suno's team. The scripted login is fragile. Use the visible browser + manual login + cookie save/load flow instead.

**"Playwright not installed"**: Run `playwright install chromium` in the server environment. This installs the Chromium browser binary that Playwright needs.

**Cookie file not found**: The `recon_output/` directory must contain the cookie file. Default name is `suno_cookies.json`. Use `recon_save_cookies("custom_name.json")` for custom names.

**Suno rate limiting**: Suno may temporarily block automated access if too many generations are requested rapidly. Wait 5-10 minutes between sessions.

**Audio download fails**: The track may not have finished generating. Check `suno_get_status()` before attempting download. If the track ID is invalid, check the Suno library URL for the correct ID.

**Stem download fails**: Stem availability depends on the generation model and subscription tier. Not all tracks have stems. Set `include_stems=False` if you only need the main audio file.

