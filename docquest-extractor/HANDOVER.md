# Handover Instructions for Classifier Fix

## 🎯 Current Status

**Branch**: `feature/fix-classifier-question-merging`  
**Status**: ✅ Ready for review and merge  
**Commits**: 2 commits pushed to GitHub

---

## 📝 What Was Fixed

Fixed critical bug where classifier was merging 10+ sequential questions into single entries.

**Key Fix**: Reordered state machine - question detection now happens BEFORE option detection.

**Results**:
- p1_q1: 43 options → 4 options ✅
- Questions detected: 668 → 627 (properly separated)
- No merging issues detected

---

## 🔗 Next Steps for Team

### 1. Create Pull Request (5 mins)
Visit: https://github.com/director-ram/DocForge/pull/new/feature/fix-classifier-question-merging

**PR Title**:
```
Fix: Prevent merging of sequential questions in classifier
```

**PR Description**: (Copy from CLASSIFIER_FIX_SUMMARY.md or use template below)

### 2. Code Review (Team)
- Review `scripts/classify_text.py` changes
- Check `CLASSIFIER_FIX_SUMMARY.md` for detailed explanation
- Run tests: `python scripts/classify_text.py --in data/raw_blocks.json --out data/classified_output_FIXED.json`
- Verify: `python scripts/check_first_5.py`

### 3. After PR Approval
```bash
# Switch to develop branch
git checkout develop

# Merge the feature branch
git merge feature/fix-classifier-question-merging

# Push to remote
git push origin develop

# Delete feature branch (optional)
git branch -d feature/fix-classifier-question-merging
git push origin --delete feature/fix-classifier-question-merging
```

### 4. Re-run Downstream Processes

**Update the data file** (IMPORTANT!):
```bash
# Replace old classification with fixed version
cp data/classified_output_FIXED.json data/classified_output.json
```

**Re-run AI answering** (~2 hours):
```bash
python scripts/auto_answer_with_ollama.py --model gemma2:9b
# Expected: Better accuracy on 627 properly separated questions
```

**Re-generate PDF** (~5 mins):
```bash
python scripts/generate_answered_pdf.py "Living Word.pdf" "Living Word_Complete.pdf" --answers data/ai_generated_answers.json
# Expected: Improved highlighting with proper question structure
```

---

## 🐛 Known Remaining Issues

Still missing **136 questions (17.8%)** due to:

1. **Orphaned options** - Page 1 starts with "(3)" and "(4)" but Question 1 text is missing
2. **Edge cases** - Questions with unusual formatting  
3. **Page boundaries** - Questions split across pages

**Future work needed**: Investigate PDF parsing to capture all questions.

---

## 📁 Key Files Modified

1. **scripts/classify_text.py** 
   - Complete rewrite with state machine (455 insertions, 89 deletions)
   - Main fix: Reordered detection (questions before options)

2. **scripts/analyze_missing_questions.py**
   - Updated to use `classified_output_FIXED.json`

3. **CLASSIFIER_FIX_SUMMARY.md** (NEW)
   - Comprehensive documentation of the fix
   - Test results and verification commands
   - Next steps and remaining issues

---

## 🧪 Verification Commands

```bash
# Check first question is fixed (should show 4 options)
python scripts/check_first_question.py

# Check first 5 questions (should all have 4 options)
python scripts/check_first_5.py

# Analyze overall quality
python scripts/analyze_missing_questions.py

# Run classifier
python scripts/classify_text.py --in data/raw_blocks.json --out data/classified_output_FIXED.json
```

---

## 💡 Tips for Next Developer

1. **Read CLASSIFIER_FIX_SUMMARY.md first** - Has all technical details
2. **Test locally before merge** - Verify no regressions
3. **Update data file** - Don't forget to replace `classified_output.json`
4. **Re-run downstream** - AI answering and PDF generation need fresh data
5. **Check CONTRIBUTING.md** - Follow team guidelines for any new work

---

## 📞 Questions?

- Check `CLASSIFIER_FIX_SUMMARY.md` for technical details
- Review commit messages for context: `git log --oneline`
- See test results in the summary document
- Look at `scripts/check_first_5.py` for verification examples

---

## ✅ Acceptance Criteria (How to verify fix works)

Run these commands and verify output:

```bash
# 1. First question should have 4 options
python scripts/check_first_question.py
# Expected output: "Number of options: 4"
# Expected labels: ['1', '2', '3', '4']

# 2. No merging issues detected
python scripts/analyze_missing_questions.py
# Expected: "✅ No obvious classification issues in sample"

# 3. More questions on page 1
# Should show ~12 questions on page 1 (was 6 before)
```

---

**Status**: ✅ Ready for handover  
**Blocking Issues**: None  
**Dependencies**: None  
**Estimated Review Time**: 30 minutes  
**Estimated Merge + Deploy**: 2.5 hours (mostly AI re-processing time)
