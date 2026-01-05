#!/bin/bash

HEADSET="Kraken.*Tournament"
ANALOG="Ryzen HD Audio Controller Analog Stereo"

toggle_audio() {
    current_sink_line=$(wpctl status | grep -A20 "Audio" | grep -A20 "Sinks:" | grep "\*")

    if [ -z "$current_sink_line" ]; then
        echo "Nessun sink attivo trovato, porco dio"
        exit 1
    fi

    current_id=$(echo "$current_sink_line" | grep -oE '[0-9]+' | head -n1)

    family_id=$(wpctl status | grep -A20 "Audio" | grep -A20 "Sinks:" | grep "$ANALOG" | grep -oE '[0-9]+' | head -n1)
    kraken_id=$(wpctl status | grep -A20 "Audio" | grep -A20 "Sinks:" | grep "$HEADSET" | grep -oE '[0-9]+' | head -n1)

    if [ -z "$family_id" ]; then
        echo "Sink Family non trovato, porco il clero"
        exit 1
    fi

    if [ -z "$kraken_id" ]; then
        echo "Sink Kraken non trovato, dio can"
        exit 1
    fi

    echo "Family ID: $family_id, Kraken ID: $kraken_id, Current: $current_id"

    if [ "$current_id" == "$family_id" ]; then
        echo "Switching from Family to Kraken"
        wpctl set-default "$kraken_id"
    elif [ "$current_id" == "$kraken_id" ]; then
        echo "Switching from Kraken to Family"
        wpctl set-default "$family_id"
    else
        echo "Unknown sink, defaulting to Kraken"
        wpctl set-default "$kraken_id"
    fi
}

if ! command -v wpctl &> /dev/null; then
    echo "wpctl non trovato, installalo prima di rompere i coglioni"
    exit 1
fi

toggle_audio
