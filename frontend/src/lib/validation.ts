import { z } from "zod";

export const formSchema = z.object({
  user_question: z.string().trim().min(1, "用户问题不能为空").max(4000, "用户问题过长"),
  model_answer: z.string().trim().min(1, "模型回复不能为空").max(16000, "模型回复过长"),
  images: z.array(z.instanceof(File)).max(8, "最多上传 8 张图片"),
  text_model: z.string(),
  vision_model: z.string(),
});

export function validateImageFiles(files: File[]): string | null {
  const allowed = new Set(["image/png", "image/jpeg", "image/webp"]);
  for (const file of files) {
    if (!allowed.has(file.type)) {
      return "仅支持 PNG、JPG、JPEG、WEBP 图片";
    }
    if (file.size > 10 * 1024 * 1024) {
      return "单张图片不能超过 10MB";
    }
  }
  return null;
}
