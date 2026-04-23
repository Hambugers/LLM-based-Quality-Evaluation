export interface SampleCase {
  id: string;
  title: string;
  user_question: string;
  model_answer: string;
  images: string[];
}

export const sampleCases: SampleCase[] = [
  {
    id: "case-1",
    title: "商务车推荐",
    user_question: "30万以内商务车推荐",
    model_answer: `30万以内的商务车市场有众多选择，以下为你推荐几款性价比较高的车型：

1. 别克 GL8 ES 陆尊
   指导价 23.29-36.99 万，经销商报价 21.29 万起。该车是国内 MPV 市场的领军者，拥有宜商宜家的黄金比例车身，车长超过 5.2 米，轴距接近 3.1 米，提供宽敞的 7 座布局，第二排贵宾座椅舒适性高，还配备双联屏，第三排头部空间 945mm，同级最大，综合产品力出色，非常适合商务接待和满员出行。
   附车型图片。
2. 本田奥德赛混动
   指导价 23.58-35.48 万，经销商报价 20.58 万起。作为国内混动 MPV 的开创者，它油耗低，实测综合油耗 5.8L/100km，造型时尚，低地台设计方便老人小孩上下车，空间灵活度高，其魔术座椅能满足多种使用需求。虽然车长未达到 4.9 米，但 2.9 米的轴距足以满足 7 座布局需求，适合商务通勤和家庭出行兼顾的场景。
   附车型图片。
3. 传祺 E9
   指导价 26.58-36.58 万，经销商报价 23.58 万起。车辆搭载 8155 芯片和 L2+ 级智驾，科技配置丰富，2.0TM 混动搭配 25.57 度大电池，能耗表现优秀，后段加速强劲，没电工况油耗 6L/100km，CDC 悬架也能提升驾乘舒适性，无论是商务接待还是全家出行都能胜任。
   附车型图片。`,
    images: ["/sample-assets/1-1.PNG", "/sample-assets/1-2.PNG", "/sample-assets/1-3.PNG"],
  },
  {
    id: "case-2",
    title: "甲骨文字形",
    user_question: "森和林的甲骨文长什么样",
    model_answer:
      "甲骨文“林”字像两（多）棵树并排，是由两个“木”字组成的会意字，表示大量的、成排成片的树木。甲骨文“森”字由三个“木”构成，或并列排列，或成“品”字形分布，合三“木”以会树木众多之意。\n同时附了多张图片，图片内容混杂，包括字形示意图、饰品图、资料/书封图、节目截图类图片等。",
    images: [
      "/sample-assets/2-1.PNG",
      "/sample-assets/2-2.PNG",
      "/sample-assets/2-3.PNG",
      "/sample-assets/2-4.PNG",
      "/sample-assets/2-5.PNG",
      "/sample-assets/2-6.PNG",
    ],
  },
];

export async function loadSampleImages(sample: SampleCase): Promise<File[]> {
  const files = await Promise.all(
    sample.images.map(async (url) => {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`样例图片加载失败：${url}`);
      }
      const blob = await response.blob();
      const filename = url.split("/").pop() ?? "sample.png";
      return new File([blob], filename, { type: blob.type || "image/png" });
    }),
  );
  return files;
}
