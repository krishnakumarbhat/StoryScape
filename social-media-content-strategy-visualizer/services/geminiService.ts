import { GoogleGenAI } from "@google/genai";
import { SocialPlatform } from '../types';

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

const getPrompt = (
  platform: SocialPlatform, 
  topic: string,
  url?: string,
  context?: { platform: SocialPlatform; content: string }
): string => {
  if (context) {
    return `You are a social media strategist repurposing content. 
Based on the following "${context.platform}" post:
---
${context.content}
---
Now, create a new, engaging post for ${platform} that builds upon or adapts this idea. The overarching topic is "${topic}". Ensure the new post is tailored specifically for the ${platform} audience.`;
  }
  
  if (url) {
    return `Analyze the content from this URL: ${url}. Based on that analysis, generate a compelling ${platform} post about "${topic}". The post should capture the essence of the URL's content while being perfectly formatted for ${platform}.`;
  }

  switch (platform) {
    case SocialPlatform.YouTube:
      return `Generate 3 engaging YouTube video ideas about "${topic}". For each idea, provide a catchy title and a brief 2-3 sentence description. Format the response as a list.`;
    case SocialPlatform.LinkedIn:
      return `Write a professional and insightful LinkedIn post about "${topic}". Include relevant hashtags. The tone should be authoritative yet approachable.`;
    case SocialPlatform.X:
      return `Generate a concise and impactful X (formerly Twitter) post about "${topic}". Include 2-3 relevant hashtags. Keep it under 280 characters.`;
    case SocialPlatform.Reddit:
      return `Write a Reddit post for a general audience about "${topic}". The post should be simple, clear, and engaging, suitable for a subreddit like r/explainlikeimfive. Start with a catchy title.`;
    case SocialPlatform.Instagram:
      return `Generate an engaging caption for an Instagram Reel or post about "${topic}". The caption should be attention-grabbing, include a call-to-action, and suggest 3-5 relevant trending hashtags.`;
    default:
      return `Generate a social media post about "${topic}".`;
  }
};

export const generateContent = async (
  platform: SocialPlatform,
  topic: string,
  url?: string,
  context?: { platform: SocialPlatform; content: string }
): Promise<string> => {
  try {
    const prompt = getPrompt(platform, topic, url, context);
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: prompt,
    });
    
    return response.text;
  } catch (error) {
    console.error("Error generating content:", error);
    throw new Error("Failed to generate content from AI. Please try again.");
  }
};