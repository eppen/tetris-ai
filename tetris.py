#!/usr/bin/env python3
"""
俄罗斯方块游戏 - 带AI玩家版本
使用Pygame库实现
"""

import pygame
import random
import sys
import time
import os
from pygame.locals import *

# 游戏常量
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
SIDEBAR_WIDTH = 200

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 120, 255)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (50, 50, 50)

# 方块形状定义
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 0, 1]],  # J
    [[0, 1, 1], [1, 1, 0]],  # S
    [[1, 1, 0], [0, 1, 1]]   # Z
]

# 方块颜色
SHAPE_COLORS = [CYAN, YELLOW, MAGENTA, ORANGE, BLUE, GREEN, RED]

# 最高分保存文件（与脚本同目录）
HIGH_SCORE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tetris_highscore.txt")


def get_chinese_font(size, bold=False):
    """获取支持中文的字体，避免显示成方块或乱码"""
    pygame.font.init()

    # 优先从常见系统路径加载具体字体文件（macOS 为主）
    font_paths = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/PingFang-SC.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/STSong.ttf",
        "/System/Library/Fonts/Songti.ttc",
        "/Library/Fonts/Microsoft YaHei.ttf",
        "/Library/Fonts/SimHei.ttf",
        "/Library/Fonts/SimSun.ttf",
    ]

    for path in font_paths:
        if os.path.exists(path):
            try:
                return pygame.font.Font(path, size)
            except Exception:
                continue

    # 再尝试通过字体名称匹配
    candidates = [
        "PingFang SC",
        "Heiti SC",
        "STHeiti",
        "Songti SC",
        "Hiragino Sans GB",
        "Microsoft YaHei",
        "SimHei",
        "SimSun",
    ]
    for name in candidates:
        try:
            matched = pygame.font.match_font(name, bold=bold)
            if matched:
                return pygame.font.Font(matched, size)
        except Exception:
            continue

    # 兜底：退回默认字体（可能还是没有中文，但不至于崩溃）
    return pygame.font.SysFont(None, size, bold=bold)

class Tetromino:
    """俄罗斯方块中的一个方块"""
    def __init__(self):
        self.shape_idx = random.randint(0, len(SHAPES) - 1)
        self.shape = SHAPES[self.shape_idx]
        self.color = SHAPE_COLORS[self.shape_idx]
        self.x = GRID_WIDTH // 2 - len(self.shape[0]) // 2
        self.y = 0
        
    def rotate(self):
        """旋转方块"""
        rows = len(self.shape)
        cols = len(self.shape[0])
        rotated = [[0 for _ in range(rows)] for _ in range(cols)]
        
        for r in range(rows):
            for c in range(cols):
                rotated[c][rows - 1 - r] = self.shape[r][c]
        
        return rotated
    
    def get_positions(self):
        """获取方块所有格子的位置"""
        positions = []
        for r in range(len(self.shape)):
            for c in range(len(self.shape[0])):
                if self.shape[r][c]:
                    positions.append((self.x + c, self.y + r))
        return positions

class TetrisAI:
    """俄罗斯方块AI玩家"""
    def __init__(self, game):
        self.game = game
        self.ai_enabled = False
        self.ai_speed = 0.5  # AI决策间隔（秒）- 稍微慢一点更稳定
        self.last_ai_time = 0
        self.current_plan = []
        self.plan_index = 0
        self.debug_mode = False  # 调试模式开关
        
    def enable(self):
        """启用AI"""
        self.ai_enabled = True
        self.current_plan = []
        self.plan_index = 0
        
    def disable(self):
        """禁用AI"""
        self.ai_enabled = False
        self.current_plan = []
        self.plan_index = 0
        
    def evaluate_position(self, piece, x, y, rotation):
        """评估一个位置的得分（分数越低越好）"""
        temp_board = [row[:] for row in self.game.board]
        for pos_x, pos_y in self.get_piece_positions(piece.shape, x, y, rotation):
            if 0 <= pos_y < GRID_HEIGHT and 0 <= pos_x < GRID_WIDTH:
                temp_board[pos_y][pos_x] = 1

        score = 0

        # 整体高度惩罚（越高越差）
        column_heights = self.get_column_heights(temp_board)
        total_height = sum(column_heights)
        score += total_height * 5

        # 空洞惩罚（权重最高）
        holes = self.count_holes(temp_board)
        score += holes * 80

        # 消行奖励（多行强烈偏好）
        complete_lines = self.count_complete_lines(temp_board)
        score -= complete_lines * 400

        # 凹凸不平惩罚
        bumpiness = self.calculate_bumpiness(temp_board)
        score += bumpiness * 3

        # 顶部溢出惩罚
        if self.would_cause_game_over(temp_board):
            score += 10000
        
        return score

    def evaluate_board(self, board):
        """评估一个棋盘状态的得分（分数越低越好），用于下一个方块的 look-ahead"""
        score = 0
        column_heights = self.get_column_heights(board)
        total_height = sum(column_heights)
        score += total_height * 5
        holes = self.count_holes(board)
        score += holes * 80
        complete_lines = self.count_complete_lines(board)
        score -= complete_lines * 400
        bumpiness = self.calculate_bumpiness(board)
        score += bumpiness * 3
        if self.would_cause_game_over(board):
            score += 10000
        return score

    def get_best_score_for_piece(self, board, piece):
        """在给定棋盘上放置该方块，返回能得到的最好得分（越低越好）"""
        best_score = float('inf')
        shape = piece.shape
        for rotation in range(4):
            rotated_shape = shape
            for _ in range(rotation):
                rows, cols = len(rotated_shape), len(rotated_shape[0])
                rotated = [[0] * rows for _ in range(cols)]
                for r in range(rows):
                    for c in range(cols):
                        rotated[c][rows - 1 - r] = rotated_shape[r][c]
                rotated_shape = rotated
            shape_w, shape_h = len(rotated_shape[0]), len(rotated_shape)
            for x in range(-shape_w + 1, GRID_WIDTH):
                valid_x = all(0 <= x + c < GRID_WIDTH for c in range(shape_w))
                if not valid_x:
                    continue
                y = 0
                while y <= GRID_HEIGHT - shape_h:
                    positions = self.get_piece_positions(piece.shape, x, y, rotation)
                    valid = all(0 <= pos_y < GRID_HEIGHT and 0 <= pos_x < GRID_WIDTH and not board[pos_y][pos_x] for pos_x, pos_y in positions)
                    if not valid:
                        break
                    next_positions = self.get_piece_positions(piece.shape, x, y + 1, rotation)
                    at_bottom = any(pos_y >= GRID_HEIGHT or (0 <= pos_y < GRID_HEIGHT and board[pos_y][pos_x]) for pos_x, pos_y in next_positions)
                    if at_bottom:
                        temp_board = [row[:] for row in board]
                        for pos_x, pos_y in positions:
                            if 0 <= pos_y < GRID_HEIGHT and 0 <= pos_x < GRID_WIDTH:
                                temp_board[pos_y][pos_x] = 1
                        best_score = min(best_score, self.evaluate_board(temp_board))
                        break
                    y += 1
        return best_score if best_score != float('inf') else 10000

    def get_column_heights(self, board):
        """获取每列的高度"""
        heights = []
        for x in range(GRID_WIDTH):
            height = 0
            for y in range(GRID_HEIGHT):
                if board[y][x]:
                    height = GRID_HEIGHT - y
                    break
            heights.append(height)
        return heights
    
    def would_cause_game_over(self, board):
        """检查这个位置是否会导致游戏结束（顶部有方块）"""
        # 检查顶部两行是否有方块
        for y in range(2):
            for x in range(GRID_WIDTH):
                if board[y][x]:
                    return True
        return False
    
    def get_piece_positions(self, shape, x, y, rotation):
        """获取指定旋转状态下方块的位置"""
        # 应用旋转
        rotated_shape = shape
        for _ in range(rotation):
            rows = len(rotated_shape)
            cols = len(rotated_shape[0])
            rotated = [[0 for _ in range(rows)] for _ in range(cols)]
            for r in range(rows):
                for c in range(cols):
                    rotated[c][rows - 1 - r] = rotated_shape[r][c]
            rotated_shape = rotated
        
        positions = []
        for r in range(len(rotated_shape)):
            for c in range(len(rotated_shape[0])):
                if rotated_shape[r][c]:
                    positions.append((x + c, y + r))
        return positions
    
    def count_holes(self, board):
        """计算空洞数量（空洞：上方有方块的空白格子）"""
        holes = 0
        for x in range(GRID_WIDTH):
            # 找到该列的最高方块
            top_block_y = None
            for y in range(GRID_HEIGHT):
                if board[y][x]:
                    top_block_y = y
                    break
            
            # 如果这一列有方块，检查它下面的空洞
            if top_block_y is not None:
                for y in range(top_block_y + 1, GRID_HEIGHT):
                    if not board[y][x]:
                        holes += 1
        
        return holes
    
    def count_complete_lines(self, board):
        """计算完整行数"""
        complete = 0
        for y in range(GRID_HEIGHT):
            if all(board[y]):
                complete += 1
        return complete
    
    def calculate_bumpiness(self, board):
        """计算棋盘表面的凹凸不平程度"""
        heights = []
        for x in range(GRID_WIDTH):
            height = 0
            for y in range(GRID_HEIGHT):
                if board[y][x]:
                    height = GRID_HEIGHT - y
                    break
            heights.append(height)
        
        bumpiness = 0
        for i in range(len(heights) - 1):
            bumpiness += abs(heights[i] - heights[i + 1])
        return bumpiness
    
    def find_best_move(self):
        """寻找最佳移动"""
        best_score = float('inf')
        best_plan = []
        best_x = 0
        best_y = 0
        best_rotation = 0
        
        piece = self.game.current_piece
        shape_names = ['I', 'O', 'T', 'L', 'J', 'S', 'Z']
        current_shape = shape_names[piece.shape_idx]
        
        positions_evaluated = 0
        
        # 尝试所有可能的旋转（0-3次）
        for rotation in range(4):
            # 获取当前旋转状态下的形状
            rotated_shape = piece.shape
            for _ in range(rotation):
                rows = len(rotated_shape)
                cols = len(rotated_shape[0])
                rotated = [[0 for _ in range(rows)] for _ in range(cols)]
                for r in range(rows):
                    for c in range(cols):
                        rotated[c][rows - 1 - r] = rotated_shape[r][c]
                rotated_shape = rotated
            
            shape_width = len(rotated_shape[0])
            shape_height = len(rotated_shape)
            
            # 尝试所有可能的水平位置（考虑边界）
            for x in range(-shape_width + 1, GRID_WIDTH):
                # 检查水平位置是否有效
                valid_x = True
                for test_x in range(x, x + shape_width):
                    if test_x < 0 or test_x >= GRID_WIDTH:
                        valid_x = False
                        break
                
                if not valid_x:
                    continue
                
                # 计算方块能下落到的最大高度
                y = 0
                while y < GRID_HEIGHT - shape_height + 1:
                    # 检查当前位置是否有效
                    valid = True
                    for pos_x, pos_y in self.get_piece_positions(piece.shape, x, y, rotation):
                        if pos_y >= GRID_HEIGHT or (pos_y >= 0 and self.game.board[pos_y][pos_x]):
                            valid = False
                            break
                    
                    if not valid:
                        break
                    
                    # 检查下一个位置是否碰撞
                    next_valid = True
                    for pos_x, pos_y in self.get_piece_positions(piece.shape, x, y + 1, rotation):
                        if pos_y >= GRID_HEIGHT or (pos_y >= 0 and self.game.board[pos_y][pos_x]):
                            next_valid = False
                            break
                    
                    if not next_valid:
                        # 找到最终位置
                        break
                    
                    y += 1
                
                # 确保位置有效
                if y < 0:
                    continue
                
                # 评估这个位置（当前方块）
                score = self.evaluate_position(piece, x, y, rotation)
                # 考虑下一个方块：在放置当前方块后的棋盘上，下一个方块能拿到的最好分数
                temp_board = [row[:] for row in self.game.board]
                for pos_x, pos_y in self.get_piece_positions(piece.shape, x, y, rotation):
                    if 0 <= pos_y < GRID_HEIGHT and 0 <= pos_x < GRID_WIDTH:
                        temp_board[pos_y][pos_x] = 1
                next_best = self.get_best_score_for_piece(temp_board, self.game.next_piece)
                total_score = score + 0.5 * next_best
                positions_evaluated += 1

                if total_score < best_score:
                    best_score = total_score
                    best_x = x
                    best_y = y
                    best_rotation = rotation
                    # 生成移动计划
                    best_plan = self.generate_move_plan(piece, x, y, rotation)
        
        # 调试输出
        if self.debug_mode and best_plan:
            print(f"AI决策: 方块 {current_shape}, 旋转 {best_rotation}, 位置 ({best_x}, {best_y}), 分数 {best_score:.1f}")
            print(f"评估了 {positions_evaluated} 个位置")
        
        # 如果没有找到有效移动，返回一个安全的后备计划
        if not best_plan:
            if self.debug_mode:
                print("AI警告: 未找到有效移动，使用后备计划")
            # 尝试简单的右移然后硬降落
            best_plan = ['right', 'hard_drop']
        
        return best_plan
    
    def generate_move_plan(self, piece, target_x, target_y, target_rotation):
        """生成移动计划"""
        plan = []
        current_x = piece.x
        current_y = piece.y
        
        # 计算需要的旋转次数
        rotations_needed = target_rotation % 4
        
        # 添加旋转操作
        for _ in range(rotations_needed):
            plan.append('rotate')
        
        # 计算水平移动
        move_x = target_x - current_x
        if move_x > 0:
            for _ in range(move_x):
                plan.append('right')
        elif move_x < 0:
            for _ in range(-move_x):
                plan.append('left')
        
        # 添加硬降落
        plan.append('hard_drop')
        
        return plan
    
    def update(self, dt):
        """更新AI状态"""
        if not self.ai_enabled or self.game.game_over:
            return
        
        self.last_ai_time += dt
        
        if self.last_ai_time >= self.ai_speed:
            self.last_ai_time = 0
            
            # 如果没有计划，生成新的计划
            if not self.current_plan or self.plan_index >= len(self.current_plan):
                self.current_plan = self.find_best_move()
                self.plan_index = 0
            
            # 执行计划中的下一个动作
            if self.current_plan and self.plan_index < len(self.current_plan):
                action = self.current_plan[self.plan_index]
                self.execute_action(action)
                self.plan_index += 1
    
    def execute_action(self, action):
        """执行一个动作"""
        if action == 'left':
            self.game.move_piece(-1, 0)
        elif action == 'right':
            self.game.move_piece(1, 0)
        elif action == 'rotate':
            self.game.rotate_piece()
        elif action == 'hard_drop':
            self.game.hard_drop()


class TetrisGame:
    """俄罗斯方块游戏主类"""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("俄罗斯方块 - AI模式")
        self.clock = pygame.time.Clock()
        # 使用支持中文的字体，字号适当缩小
        self.font = get_chinese_font(18, bold=True)   # 标题、分数等
        self.small_font = get_chinese_font(14)        # 操作说明等小字
        
        self.ai = TetrisAI(self)
        self.high_score = 0
        self._load_high_score()
        self.is_new_high = False
        self.reset_game()

    def _load_high_score(self):
        """从文件加载最高分"""
        try:
            if os.path.exists(HIGH_SCORE_FILE):
                with open(HIGH_SCORE_FILE, "r", encoding="utf-8") as f:
                    self.high_score = max(0, int(f.read().strip()))
        except (ValueError, OSError):
            pass

    def _save_high_score(self):
        """将最高分保存到文件"""
        try:
            with open(HIGH_SCORE_FILE, "w", encoding="utf-8") as f:
                f.write(str(self.high_score))
        except OSError:
            pass

    def _set_game_over(self):
        """标记游戏结束，若得分创新高则更新并保存最高分"""
        self.game_over = True
        if self.score > self.high_score:
            self.is_new_high = True
            self.high_score = self.score
            self._save_high_score()
        else:
            self.is_new_high = False

    def reset_game(self):
        """重置游戏状态"""
        self.board = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.current_piece = Tetromino()
        self.next_piece = Tetromino()
        self.game_over = False
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.fall_speed = 0.5  # 方块下落速度（秒）
        self.fall_time = 0
        self.ai.disable()  # 重置时禁用AI
        self.is_new_high = False

    def draw_grid(self):
        """绘制游戏网格"""
        # 绘制游戏区域背景
        grid_rect = pygame.Rect(
            (SCREEN_WIDTH - SIDEBAR_WIDTH) // 2 - GRID_WIDTH * GRID_SIZE // 2,
            SCREEN_HEIGHT // 2 - GRID_HEIGHT * GRID_SIZE // 2,
            GRID_WIDTH * GRID_SIZE,
            GRID_HEIGHT * GRID_SIZE
        )
        pygame.draw.rect(self.screen, DARK_GRAY, grid_rect)
        pygame.draw.rect(self.screen, GRAY, grid_rect, 2)
        
        # 绘制网格线
        for x in range(GRID_WIDTH + 1):
            pygame.draw.line(
                self.screen, 
                (60, 60, 60),
                (grid_rect.left + x * GRID_SIZE, grid_rect.top),
                (grid_rect.left + x * GRID_SIZE, grid_rect.bottom),
                1
            )
        
        for y in range(GRID_HEIGHT + 1):
            pygame.draw.line(
                self.screen, 
                (60, 60, 60),
                (grid_rect.left, grid_rect.top + y * GRID_SIZE),
                (grid_rect.right, grid_rect.top + y * GRID_SIZE),
                1
            )
        
        return grid_rect
    
    def draw_board(self, grid_rect):
        """绘制已固定的方块"""
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.board[y][x]:
                    color_idx = self.board[y][x] - 1
                    color = SHAPE_COLORS[color_idx]
                    pygame.draw.rect(
                        self.screen,
                        color,
                        (
                            grid_rect.left + x * GRID_SIZE + 1,
                            grid_rect.top + y * GRID_SIZE + 1,
                            GRID_SIZE - 2,
                            GRID_SIZE - 2
                        )
                    )
                    pygame.draw.rect(
                        self.screen,
                        WHITE,
                        (
                            grid_rect.left + x * GRID_SIZE + 1,
                            grid_rect.top + y * GRID_SIZE + 1,
                            GRID_SIZE - 2,
                            GRID_SIZE - 2
                        ),
                        1
                    )
    
    def draw_current_piece(self, grid_rect):
        """绘制当前下落的方块"""
        for x, y in self.current_piece.get_positions():
            if 0 <= y < GRID_HEIGHT:
                pygame.draw.rect(
                    self.screen,
                    self.current_piece.color,
                    (
                        grid_rect.left + x * GRID_SIZE + 1,
                        grid_rect.top + y * GRID_SIZE + 1,
                        GRID_SIZE - 2,
                        GRID_SIZE - 2
                    )
                )
                pygame.draw.rect(
                    self.screen,
                    WHITE,
                    (
                        grid_rect.left + x * GRID_SIZE + 1,
                        grid_rect.top + y * GRID_SIZE + 1,
                        GRID_SIZE - 2,
                        GRID_SIZE - 2
                    ),
                    1
                )
    
    def draw_sidebar(self, grid_rect):
        """绘制侧边栏信息"""
        sidebar_rect = pygame.Rect(
            grid_rect.right + 20,
            grid_rect.top,
            SIDEBAR_WIDTH - 40,
            grid_rect.height
        )
        
        # 绘制下一个方块预览（AI 启用时标注「AI会参考」）
        next_label = "下一个 (AI会参考):" if self.ai.ai_enabled else "下一个:"
        next_text = self.font.render(next_label, True, WHITE)
        self.screen.blit(next_text, (sidebar_rect.left, sidebar_rect.top))
        
        # 绘制下一个方块
        next_block_rect = pygame.Rect(
            sidebar_rect.left,
            sidebar_rect.top + 50,
            120,
            120
        )
        pygame.draw.rect(self.screen, DARK_GRAY, next_block_rect)
        pygame.draw.rect(self.screen, GRAY, next_block_rect, 2)
        
        # 计算下一个方块在预览区域中的位置
        shape = self.next_piece.shape
        block_size = 25
        shape_width = len(shape[0]) * block_size
        shape_height = len(shape) * block_size
        shape_left = next_block_rect.left + (next_block_rect.width - shape_width) // 2
        shape_top = next_block_rect.top + (next_block_rect.height - shape_height) // 2
        
        for r in range(len(shape)):
            for c in range(len(shape[0])):
                if shape[r][c]:
                    pygame.draw.rect(
                        self.screen,
                        self.next_piece.color,
                        (
                            shape_left + c * block_size + 1,
                            shape_top + r * block_size + 1,
                            block_size - 2,
                            block_size - 2
                        )
                    )
        
        # 绘制分数和等级
        y_offset = next_block_rect.bottom + 30
        
        score_text = self.font.render(f"分数: {self.score}", True, WHITE)
        self.screen.blit(score_text, (sidebar_rect.left, y_offset))

        high_score_text = self.font.render(f"最高分: {self.high_score}", True, YELLOW)
        self.screen.blit(high_score_text, (sidebar_rect.left, y_offset + 20))

        level_text = self.font.render(f"等级: {self.level}", True, WHITE)
        self.screen.blit(level_text, (sidebar_rect.left, y_offset + 50))

        lines_text = self.font.render(f"消除行数: {self.lines_cleared}", True, WHITE)
        self.screen.blit(lines_text, (sidebar_rect.left, y_offset + 90))
        
        # 绘制AI状态
        y_offset += 150
        ai_status = "AI: 启用" if self.ai.ai_enabled else "AI: 禁用"
        ai_color = GREEN if self.ai.ai_enabled else RED
        ai_text = self.small_font.render(ai_status, True, ai_color)
        self.screen.blit(ai_text, (sidebar_rect.left, y_offset))
        
        # 绘制操作说明
        y_offset += 40
        controls = [
            "操作说明:",
            "← → : 左右移动",
            "↑ : 旋转",
            "↓ : 加速下落",
            "空格 : 直接落下",
            "A : 切换AI模式",
            "R : 重新开始",
            "ESC : 退出游戏"
        ]
        
        for i, text in enumerate(controls):
            control_text = self.small_font.render(text, True, WHITE)
            self.screen.blit(control_text, (sidebar_rect.left, y_offset + i * 25))
    
    def draw_game_over(self):
        """绘制游戏结束画面"""
        if self.game_over:
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            
            game_over_text = self.font.render("游戏结束!", True, RED)
            score_text = self.font.render(f"最终分数: {self.score}", True, WHITE)
            restart_text = self.small_font.render("按 R 键重新开始", True, WHITE)
            self.screen.blit(game_over_text,
                            (SCREEN_WIDTH // 2 - game_over_text.get_width() // 2,
                             SCREEN_HEIGHT // 2 - 80))
            self.screen.blit(score_text,
                            (SCREEN_WIDTH // 2 - score_text.get_width() // 2,
                             SCREEN_HEIGHT // 2 - 40))
            if self.is_new_high:
                new_high_text = self.font.render("得分新高! 已保存", True, YELLOW)
                self.screen.blit(new_high_text,
                                (SCREEN_WIDTH // 2 - new_high_text.get_width() // 2,
                                 SCREEN_HEIGHT // 2 + 10))
            self.screen.blit(restart_text,
                            (SCREEN_WIDTH // 2 - restart_text.get_width() // 2,
                             SCREEN_HEIGHT // 2 + (70 if self.is_new_high else 50)))
    
    def check_collision(self, piece, x_offset=0, y_offset=0):
        """检查碰撞"""
        for x, y in piece.get_positions():
            new_x = x + x_offset
            new_y = y + y_offset
            
            # 检查边界
            if new_x < 0 or new_x >= GRID_WIDTH or new_y >= GRID_HEIGHT:
                return True
            
            # 检查与已固定方块的碰撞
            if new_y >= 0 and self.board[new_y][new_x]:
                return True
        
        return False
    
    def check_collision_with_params(self, piece, x_offset=0, y_offset=0, rotation=0):
        """检查带旋转参数的碰撞（用于AI）"""
        # 保存原始状态
        original_x = piece.x
        original_y = piece.y
        original_shape = piece.shape
        
        # 临时应用旋转
        if rotation > 0:
            temp_shape = piece.shape
            for _ in range(rotation):
                rows = len(temp_shape)
                cols = len(temp_shape[0])
                rotated = [[0 for _ in range(rows)] for _ in range(cols)]
                for r in range(rows):
                    for c in range(cols):
                        rotated[c][rows - 1 - r] = temp_shape[r][c]
                temp_shape = rotated
            piece.shape = temp_shape
        
        # 临时应用位移
        piece.x += x_offset
        piece.y += y_offset
        
        # 检查碰撞
        collision = self.check_collision(piece)
        
        # 恢复原始状态
        piece.x = original_x
        piece.y = original_y
        piece.shape = original_shape
        
        return collision
    
    def merge_piece(self):
        """将当前方块合并到游戏板上"""
        for x, y in self.current_piece.get_positions():
            if 0 <= y < GRID_HEIGHT and 0 <= x < GRID_WIDTH:
                self.board[y][x] = self.current_piece.shape_idx + 1
    
    def clear_lines(self):
        """清除已填满的行并计算分数"""
        lines_to_clear = []
        
        for y in range(GRID_HEIGHT):
            if all(self.board[y]):
                lines_to_clear.append(y)
        
        if not lines_to_clear:
            return 0
        
        # 从下往上清除行
        for line in sorted(lines_to_clear, reverse=True):
            del self.board[line]
            self.board.insert(0, [0 for _ in range(GRID_WIDTH)])
        
        # 计算分数
        cleared = len(lines_to_clear)
        self.lines_cleared += cleared
        
        # 根据一次消除的行数给予不同分数
        if cleared == 1:
            self.score += 100 * self.level
        elif cleared == 2:
            self.score += 300 * self.level
        elif cleared == 3:
            self.score += 500 * self.level
        elif cleared == 4:  # Tetris!
            self.score += 800 * self.level
        
        # 更新等级（每清除10行升一级）
        self.level = self.lines_cleared // 10 + 1
        self.fall_speed = max(0.05, 0.5 - (self.level - 1) * 0.05)
        
        return cleared
    
    def move_piece(self, dx, dy):
        """移动当前方块"""
        if not self.check_collision(self.current_piece, dx, dy):
            self.current_piece.x += dx
            self.current_piece.y += dy
            return True
        return False
    
    def rotate_piece(self):
        """旋转当前方块"""
        original_shape = self.current_piece.shape
        self.current_piece.shape = self.current_piece.rotate()
        
        # 如果旋转后发生碰撞，尝试左右移动来调整位置
        if self.check_collision(self.current_piece):
            # 尝试向右移动
            if not self.check_collision(self.current_piece, 1, 0):
                self.current_piece.x += 1
            # 尝试向左移动
            elif not self.check_collision(self.current_piece, -1, 0):
                self.current_piece.x -= 1
            # 如果都不行，恢复原来的形状
            else:
                self.current_piece.shape = original_shape
    
    def hard_drop(self):
        """硬降落：直接落到底部"""
        while self.move_piece(0, 1):
            pass
        
        # 固定方块并生成新的
        self.merge_piece()
        self.clear_lines()
        self.current_piece = self.next_piece
        self.next_piece = Tetromino()

        # 检查游戏是否结束
        if self.check_collision(self.current_piece):
            self._set_game_over()

    def update(self, dt):
        """更新游戏状态"""
        if self.game_over:
            return
        
        self.fall_time += dt
        
        # 方块自动下落
        if self.fall_time >= self.fall_speed:
            self.fall_time = 0
            
            if not self.move_piece(0, 1):
                # 如果不能下落，固定方块并生成新的
                self.merge_piece()
                self.clear_lines()
                self.current_piece = self.next_piece
                self.next_piece = Tetromino()
                
                # 检查游戏是否结束
                if self.check_collision(self.current_piece):
                    self._set_game_over()

    def draw(self):
        """绘制游戏画面"""
        self.screen.fill(BLACK)
        
        # 绘制标题
        title_text = self.font.render("俄罗斯方块", True, CYAN)
        self.screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 20))
        
        # 绘制游戏区域
        grid_rect = self.draw_grid()
        self.draw_board(grid_rect)
        self.draw_current_piece(grid_rect)
        
        # 绘制侧边栏
        self.draw_sidebar(grid_rect)
        
        # 绘制游戏结束画面
        self.draw_game_over()
        
        pygame.display.flip()
    
    def run(self):
        """运行游戏主循环"""
        running = True
        
        while running:
            dt = self.clock.tick(60) / 1000.0  # 转换为秒
            
            # 处理事件
            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False
                
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        running = False
                    
                    elif event.key == K_r:
                        self.reset_game()
                    
                    elif event.key == K_a:  # A键切换AI模式
                        if self.ai.ai_enabled:
                            self.ai.disable()
                            pygame.display.set_caption("俄罗斯方块 - 手动模式")
                        else:
                            self.ai.enable()
                            pygame.display.set_caption("俄罗斯方块 - AI模式")
                    
                    if not self.game_over:
                        if event.key == K_LEFT:
                            self.move_piece(-1, 0)
                        elif event.key == K_RIGHT:
                            self.move_piece(1, 0)
                        elif event.key == K_DOWN:
                            self.move_piece(0, 1)
                        elif event.key == K_UP:
                            self.rotate_piece()
                        elif event.key == K_SPACE:
                            self.hard_drop()
            
            # 更新AI状态
            self.ai.update(dt)
            
            # 更新游戏状态
            self.update(dt)
            
            # 绘制游戏
            self.draw()
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = TetrisGame()
    game.run()