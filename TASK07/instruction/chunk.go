package instruction

import "fmt"

// chunk represents an immutable list of instructions
type Chunk struct {
	ins []Instruction
}

func (c *Chunk) Len() int {
	return len(c.ins)
}

func (c *Chunk) Instruction(i int) Instruction {
	return c.ins[i]
}

// generate abstract tree string
func (c *Chunk) String() string {
	var s string
	length := c.Len()

	for i := 0; i < length; i++ {
		s += fmt.Sprintf("%4d %s\n", i, c.Instruction((i)).Instruction())
	}

	return s
}
