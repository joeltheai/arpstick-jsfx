-- ArpStick: import chords from the active MIDI take in the selected item.
-- Drag a .mid into REAPER first, run this action, then click IMPORT MIDI BUFFER.
local item = reaper.GetSelectedMediaItem(0, 0)
local take = item and reaper.GetActiveTake(item)
if not take or not reaper.TakeIsMIDI(take) then
  reaper.MB("Select a MIDI item first. You can drag a .mid file into REAPER.", "ArpStick", 0)
  return
end
local _, count = reaper.MIDI_CountEvts(take)
local notes = {}
for i = 0, count - 1 do
  local ok, _, muted, pos, _, _, pitch, velocity = reaper.MIDI_GetNote(take, i)
  if ok and not muted then notes[#notes+1] = {pos=pos, pitch=pitch, vel=velocity} end
end
table.sort(notes, function(a,b) return a.pos == b.pos and a.pitch < b.pitch or a.pos < b.pos end)
local chords, group, start = {}, nil, nil
local tolerance = math.abs(reaper.MIDI_GetPPQPosFromProjQN(take, 1) - reaper.MIDI_GetPPQPosFromProjQN(take, 0)) / 128
for _, n in ipairs(notes) do
  if not start or n.pos - start > tolerance then
    if #chords >= 128 then break end
    group = {}; chords[#chords+1] = group; start=n.pos
  end
  local duplicate = false
  for _, v in ipairs(group) do if v.pitch == n.pitch then duplicate=true end end
  if #group < 8 and not duplicate then group[#group+1] = n end
end
if #chords == 0 then reaper.MB("The selected item contains no unmuted notes.", "ArpStick", 0); return end
reaper.gmem_attach("ArpStickImport")
reaper.gmem_write(0, 0)
for i, chord in ipairs(chords) do
  for v=1,8 do
    reaper.gmem_write(16+(i-1)*16+v-1, chord[v] and chord[v].pitch or -1)
    reaper.gmem_write(24+(i-1)*16+v-1, chord[v] and math.floor(chord[v].vel/127*100+0.5) or 100)
  end
end
reaper.gmem_write(1,#chords)
reaper.gmem_write(0,1)
reaper.MB(string.format("%d chords ready. Click IMPORT MIDI BUFFER in ArpStick to fill slots from the selected slot. The first importing instance consumes this buffer.",#chords),"ArpStick",0)
