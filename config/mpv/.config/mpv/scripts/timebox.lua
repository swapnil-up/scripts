-- timebox.lua
-- Enforces a watch/break cycle while playing video in mpv.
-- Default: 7 minutes of playback, then a 3 minute forced black-screen pause.
-- After the break the video stays paused until you press SPACE to resume.
-- Mirrors LeechBlockNG's "Incremental Timeboxing" set.
--
-- State persists across files and mpv restarts, so closing mpv does not
-- refill the watch budget or skip a break.
--
-- Tune via script-opts/timebox.conf:
--   watch_minutes=7
--   break_minutes=3
--   count_paused_time=no
--   persist_state=yes
--   enabled=yes

local mp = require 'mp'
local mpopt = require 'mp.options'

local opts = {
    watch_minutes = 7,
    break_minutes = 3,
    count_paused_time = false,
    persist_state = true,
    state_file = "",
    enabled = true,
    break_text = "Break",
}

mpopt.read_options(opts, "timebox")

local watch_period = opts.watch_minutes * 60
local break_period = opts.break_minutes * 60

if watch_period <= 0 or break_period <= 0 then
    mp.msg.warn("timebox: watch/break minutes must be positive; disabling")
    opts.enabled = false
end

local function resolve_state_file()
    local path = opts.state_file
    if path == "" then
        local dir = mp.get_property("config-dir")
        if not dir or dir == "" then
            dir = mp.command_native({ "expand-path", "~/.config/mpv" })
        end
        path = dir .. "/timebox.state"
    end
    return mp.command_native({ "expand-path", path })
end

local state = "watch"       -- "watch" | "break" | "ready"
local watch_elapsed = 0
local break_remaining = break_period
local overlay = nil
local last_tick = nil
local last_save = -1e9
local state_file = resolve_state_file()

local function fmt(seconds)
    seconds = math.max(0, math.floor(seconds + 0.5))
    return string.format("%d:%02d", math.floor(seconds / 60), seconds % 60)
end

local function clear_overlay()
    if overlay then
        overlay:remove()
        overlay = nil
    end
end

local function draw_overlay(text, hint)
    local dim = mp.get_property_native("osd-dimensions")
    local w = dim and dim.w or 1280
    local h = dim and dim.h or 720

    local rect = string.format(
        "{\\an7\\pos(0,0)\\p1\\bord0\\shad0\\1c&H000000&\\1a&H00&}m 0 0 l %d 0 l %d %d l 0 %d{\\p0}",
        w, w, h, h)
    local label = string.format(
        "{\\an5\\pos(%d,%d)\\fs%d\\bord2\\shad0\\1c&HFFFFFF&}%s\\N{\\fs%d\\1c&HBBBBBB&}%s",
        w / 2, h / 2, math.max(32, math.floor(h / 12)), text,
        math.max(16, math.floor(h / 30)), hint)

    local data = rect .. "\n" .. label

    if not overlay then
        overlay = mp.create_osd_overlay("ass-events")
    end
    overlay.res_x = w
    overlay.res_y = h
    overlay.data = data
    overlay:update()
end

local function draw_break()
    draw_overlay(
        string.format("%s  %s", opts.break_text, fmt(break_remaining)),
        "No auto-resume - press SPACE when the timer ends")
end

local function draw_ready()
    draw_overlay(opts.break_text .. " over", "Press SPACE to resume")
end

local function save_state(force)
    if not opts.enabled or not opts.persist_state then return end
    local now = mp.get_time()
    if not force and now - last_save < 2 then return end
    last_save = now

    local tmp = state_file .. ".tmp"
    local f = io.open(tmp, "w")
    if not f then
        mp.msg.warn("timebox: cannot write state file " .. state_file)
        return
    end
    f:write("state=" .. state .. "\n")
    f:write(string.format("watch_elapsed=%.3f\n", watch_elapsed))
    if state == "break" then
        f:write(string.format("break_deadline=%.3f\n", os.time() + break_remaining))
    end
    f:close()
    os.rename(tmp, state_file)
end

local function resume_watch()
    if state ~= "ready" then return end
    state = "watch"
    watch_elapsed = 0
    break_remaining = break_period
    clear_overlay()
    mp.remove_key_binding("timebox-resume")
    mp.set_property_bool("pause", false)
    mp.msg.info("timebox: resumed by SPACE, watching")
    save_state(true)
end

local function bind_ready()
    mp.add_forced_key_binding("SPACE", "timebox-resume", resume_watch)
end

local function load_state()
    if not opts.enabled or not opts.persist_state then return end
    local f = io.open(state_file, "r")
    if not f then return end

    local data = {}
    for line in f:lines() do
        local k, v = line:match("^%s*([%a_]+)%s*=%s*(.-)%s*$")
        if k then data[k] = v end
    end
    f:close()

    local saved = data.state
    if saved == "watch" then
        state = "watch"
        watch_elapsed = tonumber(data.watch_elapsed) or 0
        watch_elapsed = math.max(0, math.min(watch_elapsed, watch_period))
    elseif saved == "break" then
        local deadline = tonumber(data.break_deadline)
        if not deadline then return end
        local remain = deadline - os.time()
        if remain > 0 then
            state = "break"
            break_remaining = math.min(remain, break_period)
            watch_elapsed = 0
        else
            state = "ready"
            break_remaining = break_period
            watch_elapsed = 0
            bind_ready()
        end
    elseif saved == "ready" then
        state = "ready"
        break_remaining = break_period
        watch_elapsed = 0
        bind_ready()
    else
        return
    end

    mp.msg.info(string.format(
        "timebox: restored state=%s elapsed=%.1fs remaining=%.1fs",
        state, watch_elapsed, break_remaining))
end

local function start_break()
    state = "break"
    break_remaining = break_period
    watch_elapsed = 0
    if not mp.get_property_bool("pause") then
        mp.set_property_bool("pause", true)
    end
    mp.msg.info("timebox: break started")
    draw_break()
    save_state(true)
end

local function end_break()
    state = "ready"
    watch_elapsed = 0
    break_remaining = break_period
    mp.msg.info("timebox: break over, waiting for SPACE")
    draw_ready()
    bind_ready()
    save_state(true)
end

local function tick()
    local now = mp.get_time()
    local dt = last_tick and (now - last_tick) or 0
    last_tick = now

    if not opts.enabled then return end
    if dt <= 0 then return end

    if state == "watch" then
        local idle = mp.get_property_bool("idle-active")
        local eof = mp.get_property_bool("eof-reached")
        local paused = mp.get_property_bool("pause")
        if not idle and not eof and (not paused or opts.count_paused_time) then
            watch_elapsed = watch_elapsed + dt
            if watch_elapsed >= watch_period then
                start_break()
            else
                save_state(false)
            end
        end
    elseif state == "break" then
        if not mp.get_property_bool("pause") then
            mp.set_property_bool("pause", true)
        end
        break_remaining = break_remaining - dt
        if break_remaining <= 0 then
            end_break()
        else
            draw_break()
            save_state(false)
        end
    elseif state == "ready" then
        if not mp.get_property_bool("pause") then
            mp.set_property_bool("pause", true)
        end
        draw_ready()
    end
end

mp.register_event("file-loaded", function()
    last_tick = mp.get_time()
    if state == "break" then
        mp.set_property_bool("pause", true)
        draw_break()
    elseif state == "ready" then
        mp.set_property_bool("pause", true)
        draw_ready()
    end
end)

mp.register_event("end-file", function()
    save_state(true)
end)

mp.register_event("shutdown", function()
    save_state(true)
end)

load_state()

mp.add_periodic_timer(0.1, tick)
