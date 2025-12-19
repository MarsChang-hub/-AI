export enum Gender {
  MALE = '男',
  FEMALE = '女',
  OTHER = '其他'
}

export interface CustomerProfile {
  birthday: string;
  gender: Gender;
  occupation: string;
  interests: string;
  income: string;
  history: string;
  quotes: string; // "He/She Said"
  targetProduct: string; // New field: The product the agent wants to sell
}

export interface AnalysisResult {
  text: string;
  isLoading: boolean;
  error?: string;
}