#!/usr/bin/env python3
"""
测试俄罗斯方块AI功能
"""

import pygame
import sys
import time

# 导入游戏模块
sys.path.append('.')
from tetris import TetrisGame, TetrisAI

def test_ai_basic():
    """测试AI基本功能"""
    print("=== 测试俄罗斯方块AI ===")
    
    # 创建游戏实例
    game = TetrisGame()
    
    # 获取AI实例
    ai = game.ai
    
    print("1. 测试AI启用/禁用")
    print(f"   初始状态: AI启用 = {ai.ai_enabled}")
    
    ai.enable()
    print(f"   启用后: AI启用 = {ai.ai_enabled}")
    
    ai.disable()
    print(f"   禁用后: AI启用 = {ai.ai_enabled}")
    
    print("\n2. 测试位置评估")
    ai.enable()
    
    # 测试空洞计算
    test_board = [
        [1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ] * 4  # 重复以填满20行
    
    # 临时替换游戏板
    original_board = game.board
    game.board = test_board
    
    holes = ai.count_holes(game.board)
    print(f"   空洞数量: {holes}")
    
    complete_lines = ai.count_complete_lines(game.board)
    print(f"   完整行数: {complete_lines}")
    
    bumpiness = ai.calculate_bumpiness(game.board)
    print(f"   凹凸程度: {bumpiness}")
    
    # 恢复游戏板
    game.board = original_board
    
    print("\n3. 测试最佳移动查找")
    try:
        best_plan = ai.find_best_move()
        print(f"   找到移动计划: {len(best_plan)} 个步骤")
        if best_plan:
            print(f"   第一个动作: {best_plan[0]}")
    except Exception as e:
        print(f"   错误: {e}")
    
    print("\n4. 测试AI更新")
    try:
        ai.update(0.5)  # 模拟0.5秒的时间
        print("   AI更新成功")
    except Exception as e:
        print(f"   错误: {e}")
    
    print("\n=== 测试完成 ===")
    print("\n游戏说明:")
    print("1. 运行 'python tetris.py' 启动游戏")
    print("2. 按 'A' 键切换AI模式")
    print("3. 侧边栏会显示AI状态")
    print("4. AI会自动寻找最佳位置并放置方块")

if __name__ == "__main__":
    test_ai_basic()