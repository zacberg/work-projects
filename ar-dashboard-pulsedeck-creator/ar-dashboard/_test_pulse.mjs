import { readFileSync, writeFileSync } from "fs";
import { buildPulseData } from "./pulse/pulseData.js";
const snap = JSON.parse(readFileSync("hybrid-snapshot.json", "utf-8"));
const base = JSON.parse(readFileSync("../pulse-deck-agent/pulse_data.example.json", "utf-8"));
const { data, autoFilled, blanked, topCount } = buildPulseData(snap, base);
writeFileSync("_test_pulse_data.json", JSON.stringify(data, null, 2));
console.log("auto-filled:", autoFilled.length, "| blanked:", blanked.length, "| top10:", topCount);
console.log("ar_tracker_path:", data.ar_tracker_path);
