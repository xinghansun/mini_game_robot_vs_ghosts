import pygame
from random import randint, uniform
import math
from copy import copy
from time import time

# bullet objects that can be shot in horizontal directions
class Bullet:
    def __init__(self, color, str_color, damage, cost, radius = 5, velocity = 8):
        self.color = color
        self.radius = radius
        self.damage = damage
        self.cost = cost
        self.position = None
        self.direction = None
        self.fired = False
        self.vanished = False
        self.velocity = velocity
        self.str_color = str_color
    
    def generate(self, window):
        pygame.draw.circle(surface = window, color = self.color, center = self.position, radius = self.radius)
        
    def fire(self, position = (0,0), direction = 1):
        self.fired = True
        self.position = position
        self.direction = direction

    # A bullet should disapear when it hits a target or is out of the window boundary
    def move(self, objects, x_boundary):
        if not self.fired:
            raise ValueError('The bullet has not been fired yet.')
        _ = (self.position[0] + self.velocity*self.direction, self.position[1])
        hit_target = self.hit(objects, self.position, _)
        if hit_target is not None:
            self.poition = hit_target.position
            hit_target.current_health -= self.damage
        else:
            self.position = _
            self.out_of_boundary(x_boundary)
        return self.position, hit_target
        
    def out_of_boundary(self, x_boundary):
        if not self.fired:
            raise ValueError('The bullet has not been fired yet.')
        if self.position[0] < 0 or self.position[0] > x_boundary:
            self.vanished = True
    
    def hit(self, objects:list, old_position, new_position):
        if not self.fired:
            raise ValueError('The bullet has not been fired yet.')
        on_path_targets = [o for o in objects if (o.position[1]<=old_position[1]<=o.position[1]+o._height) and ((old_position[0] <= o.position[0] <= new_position[0]) or (old_position[0] >= o.position[0] >= new_position[0]))]
        if on_path_targets:
            self.vanished = True
            return sorted(on_path_targets, key = lambda x: abs(x.position[0] - old_position[0]))[0]
        else:
            return None
    
# store obejct to keep inventory of bullets 
class Store:
    def __init__(self):
        self.merchandise = {}
    
    def append(self, merchandise_num, bullet):
        self.merchandise.update({merchandise_num:bullet})
        
    def search(self, merchandise_num):
        return copy(self.merchandise[merchandise_num])

# clip object which keeps track of unfired and fired bullets
class Clip:
    def __init__(self):
        self.clip = []
        self.fired = []
    
    def load(self, bullet:Bullet):
        self.clip.append(bullet)
        
    def shoot(self):
        if self.clip:
            _ = self.clip.pop(0)
            self.fired.append(_)
            return _
        else:
            return None
    
    def move_fired(self, objects, x_boundary):
        hit_target = []
        for bullet in self.fired:
            hit_target = bullet.move(objects, x_boundary)
        self.fired = [bullet for bullet in self.fired if not bullet.vanished]
        return hit_target
    
    def generate(self, window, x, y):
        x_pos = x
        for i in range(len(self.clip)):
            bullet = self.clip[i]
            position = (x_pos, y)
            pygame.draw.circle(surface = window, color = bullet.color, center = position, radius = bullet.radius)
            x_pos += 5 + bullet.radius*2

# coin obejct to be picked up at random locations
class Coin:
    def __init__(self, window_w, window_h, coin_image_path = 'coin.png'):
        self.window_w = window_w
        self.window_h = window_h

        self.image = pygame.image.load(coin_image_path)
        self._width = self.image.get_width()
        self._height = self.image.get_height()
        
        self.position = (randint(0, window_w - self._width), randint(0, window_h - self._height))

        self.__value = 1
    
    @property
    def value(self):
        return self.__value
    
    # coins changes its location and appear at any coordinate of the window
    def refresh(self):
        self.position = (randint(0, self.window_w - self._width), randint(0, self.window_h - self._height))
        return self.value

    def generate(self, window):
        window.blit(self.image, self.position)


# coinbag object to count the coins collected and spent
class CoinBag:
    def __init__(self, coin_image_path = 'coin.png'):
        self.__balance = 0
        self.image = pygame.image.load(coin_image_path)
    @property
    def balance(self):
        return self.__balance
    
    def earn(self, amount:int):
        self.__balance += amount
    
    def spend(self, amount:int):
        self.__balance -= amount
        
    def __str__(self):
        return f"Coins: {self.__balance}"

    def generate(self, window, x, y):
        game_font = pygame.font.SysFont("Arial", 25)
        window.blit(self.image, (x, y))
        text = game_font.render(f"X {self.__balance}", True, (255, 0, 0))
        window.blit(text, (x + self.image.get_width() + 5, y + self.image.get_height()/2 - text.get_height()/2))


# robot obejct which has the ability to move, pick up coins, shoot bullets
class Robot:
    def __init__(self, window_w, window_h, robot_image_path = 'robot.png', velocity = 5, health = 100):
        self.window_w = window_w
        self.window_h = window_h
        
        self.image = pygame.image.load(robot_image_path)
        self._width = self.image.get_width()
        self._height = self.image.get_height()
        
        self.position = (window_w/2 - self._width/2, window_h/2 - self._height/2) # robot always appear in the center of the window in the begining of the game
        
        self.velocity = velocity
        self.health = health
        self.current_health = self.health
        
        self.coin_bag = CoinBag()
        self.clip = Clip()

    # purchase from store with the input merchandise_num. nothing happens if not enough coins in the coinbag
    def purchase(self, merchandise_num, store):
        if merchandise_num not in store.merchandise:
            raise ValueError('Invalid merchandise number.')
        merchandise = store.search(merchandise_num)
        if merchandise.cost > self.coin_bag.balance:
            return
        else:
            self.clip.load(merchandise)
            self.coin_bag.spend(merchandise.cost)
        
    # pick up coin and refresh the location of the coin
    def pick_coin(self, coin):
        if (self.position[0] <= coin.position[0]+coin._width/2 <= self.position[0] + self._width) and (self.position[1] <= coin.position[1]+coin._height/2 <= self.position[1] + self._height):
            self.coin_bag.earn(coin.refresh())
        else:
            pass
        
    def shoot(self, direction):
        if direction not in [-1, 1]: # -1 shoot left; 1 shoot right
            return
        bullet = self.clip.shoot()
        if bullet is None:
            return
        bullet.fire(position = (self.position[0] + self._width/2, self.position[1] + self._height/2), direction = direction)
    
    def move(self, direction = (1,1)):
        if 0 <= self.position[0] + direction[0]*self.velocity <= self.window_w - self._width:
            x = self.position[0] + direction[0]*self.velocity
        else:
            x = self.position[0]
        if 0 <= self.position[1] + direction[1]*self.velocity <= self.window_h - self._height:
            y = self.position[1] + direction[1]*self.velocity
        else:
            y = self.position[1]
        
        self.position = (x,y)
    
    def generate(self, window):
        if self.current_health > 0:
            window.blit(self.image, self.position)


# portal object owns minion(s) that specificly belong to it. minion(s) can be destroyed but will reborn as long as the portal exists.
class Portal:
    def __init__(self, portal_image_path = 'door.png', position = (0,0), side = 'LT', health = 2, reborn_cooldown = 200):
        self.image = pygame.image.load(portal_image_path)
        self._width = self.image.get_width()
        self._height = self.image.get_height()
        
        self.health = health
        self.current_health = self.health

        self.reborn_cooldown = reborn_cooldown
        self.timer = None
        
        if side == 'LT': # portal appears at left top corner
            self.position = position
        elif side == 'RT': # right top
            self.position = (position[0] - self._width, position[1])
        elif side == 'LB': # left bottom
            self.position = (position[0], position[1] - self._height)
        elif side == 'RB': # right bottom
            self.position = (position[0] - self._width, position[1] - self._height)
        else:
            raise ValueError('Illegal side mark.')
        
        self.minion = Minion(position = self.position)
        
    def generate(self, window, target_pos):
        if self.current_health <= 0:
            self.minion.current_health = 0
            return
        window.blit(self.image, self.position)
        self.minion.generate(window, self.minion.move(target_pos))  # by integrating minion move here, minion(s) can disappear if portal is broke

    def reborn_minion(self):
        if self.current_health <= 0:
            return
        if self.minion.current_health <= 0:
            if self.timer is None:
                self.timer = self.reborn_cooldown
            self.timer -= 1
            if self.timer == 0:
                self.minion.reborn(self.position)
                self.timer = None

# father class of Minion and Boss, define basic atributes and methods
class Monster:
    def __init__(self, monster_image_path = 'monster.png', position = (0,0), velocity = 2, health = 2):
        self.image = pygame.image.load(monster_image_path)
        self._width = self.image.get_width()
        self._height = self.image.get_height()
        
        self.velocity = velocity
        self.health = health
        self.current_health = self.health
        
        self.position = position
    
    def move(self, target_pos):
        if target_pos[0] > self.position[0]:
            x = self.position[0] + self.velocity
        elif target_pos[0] < self.position[0]:
            x = self.position[0] - self.velocity 
        else:
            x = self.position[0]
        if target_pos[1] > self.position[1]:
            y = self.position[1] + self.velocity
        elif target_pos[1] < self.position[1]:
            y = self.position[1] - self.velocity
        else:
            y = self.position[1]
        
        # gives monster the ability to jitter around the position (10% chance). 
        if uniform(0,1) > 0.9:
            x += randint(-10,10)
            y += randint(-10,10)

        self.position = (x,y)
        return self.position
        
    def reborn(self, position):
        self.position = position
        self.current_health = self.health
        
    def is_dead(self):
        return True if self.current_health == 0 else False

    def generate(self, window, target_pos):
        if self.current_health <= 0:
            return
        window.blit(self.image, self.position)

    def deal_damage(self, target, radius):
        if self.current_health <= 0:
            return 
        if radius**2 >= (target.position[0] - self.position[0])**2 + (target.position[1] - self.position[1])**2:
            if target.current_health > 0:
                target.current_health -= 1


class Minion(Monster):
    def __init__(self, position):
        super().__init__()
        self.position = position
        self.health = 1
        self.current_health = 1
        self.velocity = 1.5

class Boss(Monster):
    def __init__(self, position):
        super().__init__()
        self.position = position
        self.show = False
        self.health = 20
        self.current_health = 20
        self.velocity = 1
        self.ring_angle = 0
        self.ring_radius = 80
        self.n_minions = 4

    def stage(self):
        self.show = True

    def move(self, target_pos):
        if uniform(0,1) >= 0.995: # gives boss the ability to blink to the target position (0.005% chance). 
            self.position = (uniform(*sorted([self.position[0],target_pos[0]])), uniform(*sorted([self.position[1],target_pos[1]])))
        if target_pos[0] > self.position[0]:
            x = self.position[0] + self.velocity
        elif target_pos[0] < self.position[0]:
            x = self.position[0] - self.velocity
        else:
            x = self.position[0]
        if target_pos[1] > self.position[1]:
            y = self.position[1] + self.velocity
        elif target_pos[1] < self.position[1]:
            y = self.position[1] - self.velocity
        else:
            y = self.position[1]
        
        self.position = (x,y)
        return self.position

    def generate(self, window, target_pos):
        if self.current_health <= 0:
            return
        window.blit(self.image, self.move(target_pos))
        # boss has a rotating ring of minions around it to deal damage
        window.blits([(self.image, (self.position[0]+self._width/2+math.cos(self.ring_angle + i*6.28/self.n_minions)*self.ring_radius-self._width/2, self.position[1]+self._height/2+math.sin(self.ring_angle + i*6.28/self.n_minions)*self.ring_radius-self._height/2)) for i in range(self.n_minions)])
        self.ring_angle += 0.05

class Game:
    def __init__(self):
        pygame.init()
        
        self.window_w, self.window_h = 640,640
        self.window = pygame.display.set_mode((self.window_w, self.window_h + 100))
        pygame.display.set_caption("Mini Game -- by Xinghan Sun")

        self.game_font_small = pygame.font.SysFont("Arial", 15)
        self.game_font = pygame.font.SysFont("Arial", 25)
        self.game_font_large = pygame.font.SysFont("Arial", 100)
        
        self.clock = pygame.time.Clock()
        
        self.to_left, self.to_right, self.to_up, self.to_down = False, False, False, False

        self.show_help = False

        self.init_time = None
        self.end_time = None

    def new_game(self):
        self.init_time = time()
        self.end_time = None
        self.robot = Robot(self.window_w, self.window_h)

        self.boss = Boss(position = (0,0))
        self.portal_1 = Portal(position = (self.window_w/10*1,self.window_h/10*1), side = 'LT')
        self.portal_2 = Portal(position = (self.window_w/10*9,self.window_h/10*1), side = 'RT')
        self.portal_3 = Portal(position = (self.window_w/10*1,self.window_h/10*9), side = 'LB')
        self.portal_4 = Portal(position = (self.window_w/10*9,self.window_h/10*9), side = 'RB')
        self.portals = [self.portal_1, self.portal_2, self.portal_3, self.portal_4]
        
        self.coin = Coin(window_w = self.window_w, window_h = self.window_h)

        self.store = Store()
        # The bullet has atributes of (color, damage, cost, radius = 5, velocity = 8)
        self.store.append(1, Bullet(color = (255,0,0), str_color = "RED", damage = 1, cost = 1))
        self.store.append(2, Bullet(color = (0,255,0), str_color = "GREEN", damage = 3, cost = 2, velocity = 4))
        self.store.append(3, Bullet(color = (0,0,255), str_color = "BLUE", damage = 5, cost = 3, velocity = 2))
        
    
    def main(self):
        while True:
            self.check_events() # monitor keyboard actions
            self.check_portals() # remove broken portal from self.portals
            self.frame() # draw window and elements
    
    def check_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.to_left = True
                if event.key == pygame.K_RIGHT:
                    self.to_right = True
                if event.key == pygame.K_UP:
                    self.to_up = True
                if event.key == pygame.K_DOWN:
                    self.to_down = True

                if event.key == pygame.K_1:
                    self.robot.purchase(1, self.store)
                if event.key == pygame.K_2:
                    self.robot.purchase(2, self.store)
                if event.key == pygame.K_3:
                    self.robot.purchase(3, self.store)

                if event.key == pygame.K_SPACE:
                    if self.to_left:
                        direction = -1
                    elif self.to_right:
                        direction = 1
                    else:
                        direction = 0
                    if self.robot.current_health > 0:
                        self.robot.shoot(direction = direction)

                if event.key == pygame.K_F1:
                    self.show_help = not self.show_help
                if event.key == pygame.K_F2:
                    self.new_game()
                if event.key == pygame.K_ESCAPE:
                    exit()
                    
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    self.to_left = False
                if event.key == pygame.K_RIGHT:
                    self.to_right = False
                if event.key == pygame.K_UP:
                    self.to_up = False
                if event.key == pygame.K_DOWN:
                    self.to_down = False

        x,y = 0,0
        if self.to_left:
            x = -1
        if self.to_right:
            x = 1
        if self.to_up:
            y = -1
        if self.to_down:
            y = 1
        if self.robot.current_health > 0:
            self.robot.move((x,y))
            self.robot.pick_coin(self.coin)

    def frame(self):
        self.window.fill((255,255,255))

        self.draw_hints()
        self.draw_coinbag()
        self.draw_clip()

        self.draw_portal()
        self.draw_boss()
        self.draw_cores()

        self.draw_coin()

        self.draw_robot()
        self.draw_bullets()

        self.draw_ending()

        if self.show_help:
            self.help()

        pygame.display.flip()
        self.clock.tick(60)
        
    def draw_portal(self):
        for portal in self.portals:
            portal.generate(self.window, self.robot.position)
            portal.minion.deal_damage(self.robot, portal.minion._width)
            portal.reborn_minion()
            
    def draw_robot(self):
        self.robot.generate(self.window)
        if self.robot.current_health > 0:
            health_text = self.game_font_small.render(str(self.robot.current_health), True, (255, 0, 0))
            self.window.blit(health_text, (self.robot.position[0] + self.robot._width/2 - health_text.get_width()/2, self.robot.position[1] + self.robot._height/2 + 7 - health_text.get_height()/2))

    def draw_coin(self):
        self.coin.generate(self.window)

    def draw_bullets(self):
        hit_targets = self.robot.clip.move_fired(self.get_objects(), x_boundary = self.window_w)
        for bullet in self.robot.clip.fired:
            bullet.generate(self.window)

    def draw_boss(self):
        if len(self.get_objects()) == 0:
            self.boss.stage()
        if self.boss.show:
            self.boss.generate(self.window, self.robot.position)
            self.boss.deal_damage(self.robot, 90)

    def get_objects(self):
        objects = []
        for portal in self.portals:
            # portal pos
            if portal.current_health > 0:
                objects.append(portal)
                # minion pos
                if portal.minion.current_health > 0:
                    objects.append(portal.minion)
        if self.boss.show:
            if self.boss.current_health > 0:
                objects.append(self.boss)

        return objects

    # used to visualize current health of all elements
    def draw_cores(self):
        for o in self.get_objects():
            x = o.position[0] + o._width/2
            y = o.position[1] + o._height/2
            health_text = self.game_font_small.render(str(o.current_health), True, (255, 0, 0))
            self.window.blit(health_text, (x - health_text.get_width()/2, y - health_text.get_height()/2))
            #pygame.draw.circle(surface = self.window, color = (255,0,0), center = (x,y), radius = 3)

    # judge and display appropriate endings
    def draw_ending(self):
        if self.robot.current_health <= 0:
            game_text = self.game_font_large.render("Game Over", True, (255, 0, 0))
            game_text_x = self.window_w / 2 - game_text.get_width() / 2
            game_text_y = self.window_h / 2 - game_text.get_height() / 2
            pygame.draw.rect(self.window, (0, 0, 0), (game_text_x-10, game_text_y-10, game_text.get_width()+10*2, game_text.get_height()+10))
            self.window.blit(game_text, (game_text_x, game_text_y))
            return
        if self.boss.current_health <= 0:
            if self.end_time is None:
                self.end_time = time()
            game_text = self.game_font.render(f"Cleared in {round(self.end_time - self.init_time)}s", True, (255, 0, 0))
            game_text_x = self.window_w / 2 - game_text.get_width() / 2
            game_text_y = self.window_h / 2 - game_text.get_height() / 2
            pygame.draw.rect(self.window, (0, 0, 0), (game_text_x, game_text_y, game_text.get_width(), game_text.get_height()))
            self.window.blit(game_text, (game_text_x, game_text_y))
            return

    def draw_coinbag(self):
        self.robot.coin_bag.generate(self.window, 20, self.window_h + 50)

    def draw_clip(self):
        _ = self.game_font.render("Bullets:", True, (255, 0, 0))
        self.window.blit(_, (20, self.window_h + 5))
        self.robot.clip.generate(self.window, 20+_.get_width()+10, self.window_h + 5 + _.get_height()/2)

    def draw_hints(self):
        pygame.draw.rect(self.window, (0,0,0), (0, self.window_h, self.window_w, 100))
        game_text = self.game_font_small.render("F1 = help (show/hide)", True, (255, 0, 0))
        self.window.blit(game_text, (220, self.window_h + 100 - game_text.get_height() - 10))
        game_text = self.game_font_small.render("F2 = new game", True, (255, 0, 0))
        self.window.blit(game_text, (380, self.window_h + 100 - game_text.get_height() - 10))
        game_text = self.game_font_small.render("Esc = exit game", True, (255, 0, 0))
        self.window.blit(game_text, (510, self.window_h + 100 - game_text.get_height() - 10))

    def help(self):
        rect_w = 440
        rect_h = 350
        rect_x = self.window_w/2 - rect_w/2
        rect_y = self.window_h/2 - rect_h/2
        pygame.draw.rect(self.window, (0,0,255), (rect_x, rect_y, rect_w, rect_h))
        lines = ["Left: ←", "Right: →", "Up: ↑", "Down: ↓"]
        lines += ["Shoot Left: ← + SPACE", "Shoot Right: → + SPACE"]
        for num, bullet in sorted(self.store.merchandise.items(), key = lambda x: x[0]):
            lines.append(f"Purchase {bullet.str_color} bullet (Volocity={bullet.velocity};Damage={bullet.damage};Cost={bullet.cost}): {num}")
        
        lines += ["","Note1: Minions will reborn if the portals are not broken.","Note2: Boss has chance blinking to your position."]

        last_h = rect_y + 40
        for line in lines:
            text = self.game_font_small.render(line, True, (255, 255, 255))
            self.window.blit(text, (rect_x + 10, last_h))
            last_h += text.get_height() + 5

    def check_portals(self):
        self.portals = [portal for portal in self.portals if portal.current_health > 0]

if __name__ == '__main__':
    test = Game()
    test.new_game()
    test.main()


