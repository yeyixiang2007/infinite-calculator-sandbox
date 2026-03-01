import random
from math import floor

class World:
    def __init__(self):
        self.chunk_size = 16  # Size of each chunk (16x16)
        self.chunks = {}      # Dictionary to store generated chunks: (chunk_x, chunk_y) -> [[tiles]]
        self.entities = []
        self.seed = random.randint(0, 10000)

    def get_chunk_coords(self, x, y):
        return floor(x / self.chunk_size), floor(y / self.chunk_size)

    def get_local_coords(self, x, y):
        return x % self.chunk_size, y % self.chunk_size

    def generate_chunk(self, cx, cy):
        # Deterministic random generation based on seed and coordinates
        random.seed(f"{self.seed},{cx},{cy}")

        chunk = [['.' for _ in range(self.chunk_size)] for _ in range(self.chunk_size)]

        # Terrain Generation Logic
        # 10% Obstacles '|'
        for _ in range(int(self.chunk_size * self.chunk_size * 0.1)):
            lx, ly = random.randint(0, self.chunk_size-1), random.randint(0, self.chunk_size-1)
            chunk[ly][lx] = '|'

        # 5% Numbers 0-9
        for _ in range(int(self.chunk_size * self.chunk_size * 0.05)):
            lx, ly = random.randint(0, self.chunk_size-1), random.randint(0, self.chunk_size-1)
            if chunk[ly][lx] == '.':
                chunk[ly][lx] = str(random.randint(0, 9))

        # 2% Operators
        operators = ['+', '-', '*', '/', '^', '%'] # Added new operators ^ and %
        for _ in range(int(self.chunk_size * self.chunk_size * 0.02)):
            lx, ly = random.randint(0, self.chunk_size-1), random.randint(0, self.chunk_size-1)
            if chunk[ly][lx] == '.':
                chunk[ly][lx] = random.choice(operators)

        # 1% Special Terrain: Logic Gates (Just decorative or functional later)
        # Fix logic: chunk generation should not modify other chunks
        # This was a bug in previous thought process, corrected here to only modify current chunk
        # But wait, the previous code was trying to set a random tile in the chunk.
        # Let's just add it normally.
        if random.random() < 0.2:
             lx, ly = random.randint(0, self.chunk_size-1), random.randint(0, self.chunk_size-1)
             if chunk[ly][lx] == '.':
                 chunk[ly][lx] = '&'

        # 1% Strategic Items: Reverse, Sort Asc, Sort Desc
        strategic_items = ['~', '{', '}']
        for _ in range(int(self.chunk_size * self.chunk_size * 0.01)):
            lx, ly = random.randint(0, self.chunk_size-1), random.randint(0, self.chunk_size-1)
            if chunk[ly][lx] == '.':
                chunk[ly][lx] = random.choice(strategic_items)

        return chunk

    def get_tile(self, x, y):
        cx, cy = self.get_chunk_coords(x, y)
        lx, ly = self.get_local_coords(x, y)

        if (cx, cy) not in self.chunks:
            self.chunks[(cx, cy)] = self.generate_chunk(cx, cy)

        return self.chunks[(cx, cy)][ly][lx]

    def set_tile(self, x, y, char):
        cx, cy = self.get_chunk_coords(x, y)
        lx, ly = self.get_local_coords(x, y)

        if (cx, cy) not in self.chunks:
            self.chunks[(cx, cy)] = self.generate_chunk(cx, cy)

        self.chunks[(cx, cy)][ly][lx] = char

    def is_blocked(self, x, y):
        tile = self.get_tile(x, y)
        return tile == '|'

    def add_entity(self, entity):
        self.entities.append(entity)

    def get_viewport(self, center_x, center_y, width, height):
        """Returns a 2D grid representing the visible area around center_x, center_y"""
        start_x = center_x - width // 2
        start_y = center_y - height // 2

        viewport = []
        for y in range(start_y, start_y + height):
            row = []
            for x in range(start_x, start_x + width):
                row.append(self.get_tile(x, y))
            viewport.append(row)

        return viewport, start_x, start_y
