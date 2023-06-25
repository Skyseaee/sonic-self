package instruction

type ChunkBuilder struct {
	ins       []Instruction
	loopStack []int
	finalized bool
	offset    int
}

func (c *ChunkBuilder) Finalized() *Chunk {
	if !c.CanFinalize() {
		panic("chunk build: can't finalize chunk because of unclosed loops")
	}

	c.finalized = true
	return &Chunk{ins: c.ins}
}

func (c *ChunkBuilder) IsFinalized() bool {
	return c.finalized
}

func (c *ChunkBuilder) CanFinalize() bool {
	return len(c.loopStack) == 0
}

func (c *ChunkBuilder) ChangeValue(by int8) {
	c.assertNotFinalized()
	c.optimizedPush(Value{X: byte(by), Offset: c.offset})
}

func (c *ChunkBuilder) ChangePointer(change int) {
	c.assertNotFinalized()
	c.offset += change
}

func (c *ChunkBuilder) InputByte() {
	c.assertNotFinalized()
	c.optimizedPush(Input{Offset: c.offset})
}

func (c *ChunkBuilder) OutputByte() {
	c.assertNotFinalized()
	c.push(Output{Offset: c.offset})
}

func (c *ChunkBuilder) StartLoop() {
	c.assertNotFinalized()

	c.loopStack = append(c.loopStack, len(c.ins))
	c.push(StartLoop{Offset: c.offset})
	c.offset = 0
}

func (c *ChunkBuilder) EndLoop() {
	c.assertNotFinalized()

	if len(c.loopStack) == 0 {
		panic("chunk builder: unexpected EndLoop")
	}

	last := len(c.loopStack) - 1
	start := c.loopStack[last]
	c.loopStack = c.loopStack[:last]

	body := c.ins[start+1:]
	offset := c.ins[start].MemOffset()

	// remove loops which are never executed
	if c.isRedundantLoop(start, offset) {
		c.ins = c.ins[:start] // clear instruction slice
		c.offset = offset     // reset current offset
		return
	}

	if i, ok := optimizeLoopBody(body, offset, c.offset); ok {
		c.ins = c.ins[:start]
		c.put(i...)

		c.offset = offset
		return
	}

	// optimization failed, standard loop
	c.push(EndLoop{Offset: c.offset})
	c.offset = 0
}

// check if a loop starting at the given position in the instruction chunk
// is redundant or not

// Loops which are before any other instruction are redundant as all cells
// are 0 by default. Loops which start right after the end of another loop
// or a Clear instruction are redundant as the previous loop only exits
// when the cell is zero.
func (c *ChunkBuilder) isRedundantLoop(pos, offset int) bool {
	ins := c.ins[pos-1]

	switch {
	case pos == 0:
		return true
	case ins.MemOffset() != offset:
		return false
	}

	switch v := ins.(type) {
	case Set:
		return v.X == 0
	case EndLoop:
		return true
	default:
		return false
	}
}

func (c *ChunkBuilder) assertNotFinalized() {
	if c.finalized {
		panic("chunk builder: chunk has already been finalized.")
	}
}

func (c *ChunkBuilder) last() Instruction {
	if len(c.ins) == 0 {
		return nil
	}

	return c.ins[len(c.ins)-1]
}

func (c *ChunkBuilder) pop() {
	if len(c.ins) == 0 {
		return
	}

	c.ins = c.ins[:len(c.ins)-1]
}

func (c *ChunkBuilder) put(is ...Instruction) {
	for _, i := range is {
		c.optimizedPush(i)
	}
}

// add the given instruction to the chunk after optimizing it
func (c *ChunkBuilder) optimizedPush(i Instruction) {
	if c.last() != nil && c.last().MemOffset() == i.MemOffset() {
		switch curr := i.(type) {
		case Value:
			if curr.X == 0 {
				return
			}
			switch prev := c.last().(type) {
			case Value:
				c.pop()
				if t := prev.X + curr.X; t != 0 {
					c.push(Value{X: t, Offset: curr.MemOffset()})
				}
				return
			case Set:
				c.pop()
				c.push(Set{X: prev.X + curr.X, Offset: curr.MemOffset()})
				return
			}
		case Set, Input:
			switch c.last().(type) {
			case Value, Set, Input:
				c.pop()
			}
		}
	}
	c.push(i)
}

func (c *ChunkBuilder) push(i ...Instruction) {
	c.ins = append(c.ins, i...)
}

func optimizeLoopBody(i []Instruction, start, end int) ([]Instruction, bool) {
	if end == 0 {
		switch len(i) {
		case 0:

		case 1:
			if v, ok := i[0].(Value); ok {
				return []Instruction{Set{X: 0, Offset: start + v.Offset}}, true
			}

		default:
			// else
		}
	}
	return nil, false
}
