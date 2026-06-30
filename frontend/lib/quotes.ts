export type QuoteCategory = 'analysis' | 'tryon' | 'general'

export interface LoadingQuote {
  text: string
  category: QuoteCategory
}

export const LOADING_QUOTES: LoadingQuote[] = [
  // Analysis quotes
  { text: "Measuring 478 facial landmarks. Your cheekbones have their own paragraph.", category: 'analysis' },
  { text: "Fun fact: oval faces can wear almost any frame style. Stay tuned to see if you're one of the lucky ones.", category: 'analysis' },
  { text: "Your skin undertone is being decoded. The result changes which metals and acetates look best on you.", category: 'analysis' },
  { text: "Diamond face shapes are the rarest. Fingers crossed for you.", category: 'analysis' },
  { text: "IPD measurement in progress. The average adult's is 63mm. How do you compare?", category: 'analysis' },
  { text: "Round faces + square frames = instant definition. Let's see what your face has to say about that.", category: 'analysis' },
  { text: "Warm undertone? Tortoiseshell and gold frames are about to become your best friends.", category: 'analysis' },
  { text: "Cool undertone? Silver, gunmetal, and navy frames are already warming up for you.", category: 'analysis' },
  { text: "Heart-shaped faces look stunning in round and rimless frames. We're checking if that's your story.", category: 'analysis' },
  { text: "The AI has 262,144 tokens of context to understand your face. Your jawline gets its own section.", category: 'analysis' },
  { text: "Analysing cheekbone-to-jaw ratio. Science. For glasses. On your face.", category: 'analysis' },
  { text: "Oblong faces shine in wide, bold frames — adds that perfect horizontal balance.", category: 'analysis' },
  { text: "Square jaw? Curved frames coming your way. The contrast is chef's kiss.", category: 'analysis' },
  { text: "Your face is like a great brief. We're giving it to the most talented AI in the room.", category: 'analysis' },
  { text: "Spectacles were invented in Italy around 1290. You're benefiting from 730+ years of innovation right now.", category: 'analysis' },

  // Try-on quotes
  { text: "Nano Banana is painting your portrait. Reportedly, it takes ~18 seconds. We'll hold.", category: 'tryon' },
  { text: "Your photorealistic try-on is being rendered pixel by pixel. Some pixels are especially stubborn.", category: 'tryon' },
  { text: "Still faster than driving to a store, parking, and trying on 12 frames only to be told they're sold out.", category: 'tryon' },
  { text: "The model is figuring out exactly how those temples sit on your ears. The details matter.", category: 'tryon' },
  { text: "Genuine AI magic is happening. Not the disappointing 'AR sticker on your face' kind.", category: 'tryon' },
  { text: "Titanium frames are 50% lighter than standard metal. Great trivia while we generate your look.", category: 'tryon' },
  { text: "This is a diffusion model rendering your face. 20 seconds of diffusion for a lifetime of confidence.", category: 'tryon' },
  { text: "Fun fact: Benedict Cumberbatch, David Beckham, Johnny Depp — all levelled up with glasses. You're next.", category: 'tryon' },
  { text: "The average person tries 3–4 pairs before buying. You're doing it in 20 seconds without leaving your chair.", category: 'tryon' },
  { text: "The frame colour in your try-on matches the exact product photo. No 'it looked different in person' moments.", category: 'tryon' },
  { text: "Generating photorealistic try-on. Still faster than a Lenskart store on a Saturday afternoon.", category: 'tryon' },
  { text: "A great pair of glasses is cheaper than a therapist and does 40% of the same work.", category: 'tryon' },
  { text: "The ancient Romans used emeralds to watch gladiator fights. You're getting AI try-on. Progress.", category: 'tryon' },
  { text: "We're preserving your exact skin tone, hair, expression, and background. Just adding the frames.", category: 'tryon' },
  { text: "You're 15 seconds away from seeing yourself in frames you'll actually want to buy.", category: 'tryon' },

  // General / witty
  { text: "The right frames can make you look smarter, warmer, cooler, or more authoritative. All four if you're lucky.", category: 'general' },
  { text: "Life is too short to wear boring frames.", category: 'general' },
  { text: "Your face is the canvas. Frames are the art. We're finding the right brushstroke.", category: 'general' },
  { text: "Good news: there are no ugly face shapes. There are only mismatched frame choices.", category: 'general' },
  { text: "Finding your perfect frame is like the right haircut — you'll wonder how you lived without it.", category: 'general' },
  { text: "The difference between looking good and looking great is often 2 centimetres of acetate.", category: 'general' },
  { text: "Frame width should match your face width. We've already measured yours.", category: 'general' },
  { text: "The eyes are the window to the soul. Frames are the architecture around those windows.", category: 'general' },
  { text: "400+ frames in the catalogue. We're narrowing it to the ones that actually work for your face.", category: 'general' },
  { text: "Matching frames to your face is like pairing wine with food. Both decisions matter more than you'd think.", category: 'general' },
  { text: "Blue-light glasses don't reduce eye strain. We had to tell someone. Now: about your face shape.", category: 'general' },
  { text: "Glasses are the only accessory that lives on your face, permanently, every single day. Choose wisely.", category: 'general' },
  { text: "We analyse. We recommend. We render. You just show up and look good.", category: 'general' },
  { text: "Lenskart has 2,000 stores. FrameAI has one AI and your selfie. David vs Goliath, but make it stylish.", category: 'general' },
  { text: "Style is knowing who you are, what you want to say, and finding the frames to say it.", category: 'general' },
  { text: "Rimless frames make a face look less framed. But make the person look more confident. Go figure.", category: 'general' },
  { text: "Cat-eye frames have been trending since the 1950s. Some things are perennial for a reason.", category: 'general' },
  { text: "Wayfarer frames were invented by Ray-Ban in 1952. They've been the safe choice ever since.", category: 'general' },
  { text: "If you've been picking frames by 'whatever looks okay in the mirror', today is the last time.", category: 'general' },
  { text: "The perfect pair of glasses is out there. We have 400+ suspects. We're narrowing the list.", category: 'general' },
]

export function getRandomQuote(category?: QuoteCategory): LoadingQuote {
  const pool = category
    ? LOADING_QUOTES.filter(q => q.category === category || q.category === 'general')
    : LOADING_QUOTES
  return pool[Math.floor(Math.random() * pool.length)]
}

export function getQuoteAtIndex(index: number, category?: QuoteCategory): LoadingQuote {
  const pool = category
    ? LOADING_QUOTES.filter(q => q.category === category || q.category === 'general')
    : LOADING_QUOTES
  return pool[index % pool.length]
}
