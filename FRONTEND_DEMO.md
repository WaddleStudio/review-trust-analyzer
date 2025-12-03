# Frontend Demo - Review Trust Analyzer

## 🎨 Design Highlights

### Visual Design
- **Dark Mode Theme**: Modern dark background (#0f172a) with glassmorphism effects
- **Color Coding**: 
  - 🟢 Green: Trustworthy (Trust Score ≥ 80%)
  - 🟡 Yellow: Moderate Risk (50-79%)
  - 🔴 Red: Suspicious (< 50%)
- **Animations**: Smooth transitions, micro-interactions, circular progress animation

### UI Components
1. **Input Form**
   - Platform selector (Google, Booking, Agoda, TripAdvisor)
   - Star rating selector (1-5 stars)
   - User ID field
   - Review text area

2. **Result Card**
   - Animated circular progress chart
   - Trust score percentage
   - Verdict (Trustworthy / Moderate Risk / Suspicious)
   - Detailed reasons list

## 📸 Test Results Comparison

### Test Case 1: Trustworthy Review ✅
**Input:**
- Platform: Google Maps
- Rating: 4 stars
- User ID: verified_user
- Text: "Had a wonderful stay at this hotel. The staff was friendly and helpful. The room was clean and comfortable. Would recommend to friends and family."

**Output:**
- **Trust Score**: 90%
- **Verdict**: Trustworthy (Green)
- **Reasons**: "No specific suspicious patterns detected."

**Screenshot**: `trustworthy_result_1764607553624.png`

---

### Test Case 2: Suspicious Review ⚠️
**Input:**
- Platform: Booking.com
- Rating: 5 stars
- User ID: promo_user_99
- Text: "Best hotel ever! Amazing discount! Free gift! Book now!"

**Output:**
- **Trust Score**: 10%
- **Verdict**: Suspicious (Red)
- **Reasons**: "Contains promotional keywords."

**Screenshot**: `promo_review_result_1764607580584.png`

---

### Test Case 3: Initial Suspicious Review 🔴
**Input:**
- Platform: Google
- Rating: 5 stars
- User ID: test_user
- Text: "This place is amazing! Free gift for everyone!"

**Output:**
- **Trust Score**: ~15%
- **Verdict**: Suspicious (Red)
- **Reasons**: "Contains promotional keywords."

**Screenshot**: `result_check_1_1764606197650.png`

## 🎯 Key Differences Between Versions

### Model Performance
The ML model (Logistic Regression) effectively distinguishes between:

1. **Genuine Reviews**:
   - Natural language patterns
   - Balanced sentiment
   - Specific details
   - Moderate ratings (3-4 stars)
   - No promotional language

2. **Suspicious Reviews**:
   - Promotional keywords (free, gift, discount, promo)
   - Extreme ratings (1 or 5 stars) with short text
   - Generic praise without specifics
   - High review volume from same user

### Visual Feedback
- **Trustworthy**: Green circular progress, positive message
- **Suspicious**: Red circular progress, warning message with specific reasons
- **Moderate**: Yellow circular progress, caution message

## 🔍 Feature Detection

### Text Features
- **Text Length**: Short reviews with extreme ratings are suspicious
- **Sentiment Score**: Overly positive without details
- **Promotional Keywords**: Detected: "gift", "free", "discount", "promo", "offer", "優惠", "折扣"

### User Behavior Features
- **Review Count**: High volume in short time (currently mocked)
- **IP Pattern**: Same IP multiple reviews (placeholder for future)

## 📊 Model Metrics
```
Accuracy:  0.91
Precision: 1.00
Recall:    0.47
F1 Score:  0.64
```

## 🚀 Future Enhancements
1. **Enhanced NLP**: Use BERT embeddings for semantic analysis
2. **User Profiling**: Track user history and patterns
3. **IP Analysis**: Detect review farms
4. **Time Patterns**: Identify coordinated review campaigns
5. **Cross-Platform**: Compare same user across platforms
