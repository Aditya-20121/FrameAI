# FrameAI — Product Requirements Document (PRD)
**Version:** 1.0  
**Status:** Approved

---

## Functional Requirements

### FR-01 Photo Capture
- FR-01.1: System MUST provide a camera interface with an oval face-alignment guide overlay
- FR-01.2: System MUST show real-time alignment feedback (oval turns green when face is aligned)
- FR-01.3: System MUST auto-capture after 1.5 seconds of continuous green alignment
- FR-01.4: System MUST provide a file upload fallback ("Upload a photo instead")
- FR-01.5: System MUST display instruction text: "Remove your glasses" before capture

### FR-02 Photo Validation
- FR-02.1: System MUST reject photos with no face detected (specific error message)
- FR-02.2: System MUST reject photos with more than one face detected
- FR-02.3: System MUST reject photos below 512×512 resolution
- FR-02.4: System MUST accept JPG, PNG, WEBP formats up to 10MB
- FR-02.5: System MUST return specific, actionable error messages (not generic)

### FR-03 Face Analysis
- FR-03.1: System MUST classify face shape into one of 6 categories: Oval, Round, Square, Heart, Diamond, Oblong
- FR-03.2: System MUST detect skin undertone as Warm, Cool, or Neutral
- FR-03.3: System MUST measure IPD (interpupillary distance) from landmarks
- FR-03.4: System MUST display a plain-English explanation of the user's face shape
- FR-03.5: Face analysis MUST complete in under 3 seconds

### FR-04 Recommendations
- FR-04.1: System MUST display top 5 frame recommendations after analysis
- FR-04.2: System MUST pre-load frames 6–10 and hide behind "Show 5 more" (no new request)
- FR-04.3: Each recommendation card MUST show: product image, name, style, colour, retailer, price
- FR-04.4: Each card MUST have a "Try this on →" button
- FR-04.5: Each card MUST have a "View on [Retailer] →" buy link (opens in new tab)
- FR-04.6: System MUST explain why each frame suits the user's face shape and undertone

### FR-05 Image Generation
- FR-05.1: Generation MUST be triggered per-frame — one click = one image = one generation consumed
- FR-05.2: System MUST show a micro-confirm before firing a generation: "This uses 1 of your X free tries"
- FR-05.3: Generation MUST fire only the API call for the selected frame — no batch generation
- FR-05.4: Generated image MUST appear on the specific frame card that was triggered
- FR-05.5: Generated image MUST be photorealistic — indistinguishable from a real photograph
- FR-05.6: Face identity MUST be preserved in generated image
- FR-05.7: System MUST handle user wearing glasses in input photo (inpaint removal)
- FR-05.8: Buy link MUST be prominently shown below the generated image

### FR-06 Generation Limit
- FR-06.1: Each anonymous user MUST receive exactly 3 free generations
- FR-06.2: Limit MUST be enforced server-side — client-side counter is display only
- FR-06.3: Failed generations (API error) MUST NOT decrement the counter
- FR-06.4: After 3rd generation, all "Try this on →" buttons MUST be disabled
- FR-06.5: A sign-up CTA banner MUST appear after limit is reached
- FR-06.6: Recommendations and buy links MUST remain fully functional after limit is reached
- FR-06.7: Limit MUST never reset for anonymous users

### FR-07 Data & Privacy
- FR-07.1: All user images MUST be purged after 24 hours
- FR-07.2: System MUST NOT require an account for core functionality in v1
- FR-07.3: System MUST NOT store biometric data beyond the active session

---

## Non-Functional Requirements

### NFR-01 Performance
- NFR-01.1: Face analysis pipeline MUST complete in under 3 seconds
- NFR-01.2: Image generation MUST return within 15 seconds under normal load
- NFR-01.3: Recommendation page MUST load in under 1 second after analysis
- NFR-01.4: Website MUST achieve Lighthouse performance score ≥ 85

### NFR-02 Accuracy
- NFR-02.1: Face shape classification MUST achieve ≥ 90% accuracy on a diverse test set
- NFR-02.2: Generated images MUST preserve user's facial identity (verified by manual QA)
- NFR-02.3: Frame compositing MUST align to nose bridge within ±5% of frame width

### NFR-03 Compatibility
- NFR-03.1: Website MUST work on mobile (iOS Safari, Android Chrome)
- NFR-03.2: Website MUST be responsive down to 375px viewport
- NFR-03.3: Camera guide MUST work on all browsers supporting MediaDevices.getUserMedia()
- NFR-03.4: Upload fallback MUST work on all browsers

### NFR-04 Reliability
- NFR-04.1: API (fal.ai) failure MUST be handled gracefully — user sees error, generation not counted
- NFR-04.2: System MUST handle concurrent job processing without blocking

### NFR-05 Security
- NFR-05.1: Session token MUST be HttpOnly cookie
- NFR-05.2: Generation counter MUST be validated server-side on every request
- NFR-05.3: R2 image URLs MUST be presigned with expiry (24h)

---

## Out of Scope (v1)

- User authentication / accounts
- Saved history or wishlists
- Real-time AR video overlay
- Smart mirror / hardware kiosk
- Direct purchase / checkout
- Multi-face photos
- Glasses sticker removal from product images
- Fingerprint-based session tracking
