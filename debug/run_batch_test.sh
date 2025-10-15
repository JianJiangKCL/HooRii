#!/bin/bash
# Batch test script for ElevenLabs TTS
# Processes all test texts and saves to debug/tts_output

echo "========================================================================"
echo "🎭 ElevenLabs TTS Batch Test"
echo "========================================================================"

# Create output directory with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="debug/tts_output_${TIMESTAMP}"
mkdir -p "${OUTPUT_DIR}"

echo ""
echo "📁 Output directory: ${OUTPUT_DIR}"
echo "📝 Processing 20 test files..."
echo ""

# Run the standalone TTS tool
cd /data/jj/proj/hoorii
python debug/elevenlabs_tts_standalone.py debug/voice_text "${OUTPUT_DIR}"

echo ""
echo "========================================================================"
echo "✅ Batch test complete!"
echo "========================================================================"
echo ""
echo "📊 Results:"
ls -lh "${OUTPUT_DIR}"/*.mp3 2>/dev/null | wc -l | xargs echo "   Generated files:"
du -sh "${OUTPUT_DIR}" 2>/dev/null | awk '{print "   Total size: " $1}'
echo ""
echo "🎧 Listen to files in: ${OUTPUT_DIR}/"
echo "========================================================================"


