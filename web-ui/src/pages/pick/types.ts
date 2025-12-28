/**
 * Pick 页面类型定义
 */

/** API 响应 */
export interface PickApiResponse {
    items: string[]
  }
  
  /** 状态类型 */
  export type StatusType = '' | 'ok' | 'err'
  
  /** 动画阶段配置 */
  export interface AnimationStage {
    steps: number
    delay: number
  }