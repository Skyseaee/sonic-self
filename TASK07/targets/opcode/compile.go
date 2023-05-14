package opcode

import (
	"fmt"
	"reflect"

	"code.skyseaee.com/sonic-self/TASK07/instruction"
)

func Compile(c *instruction.Chunk) []int {
	var dst []int   // result slice
	var stack []int // loop stack

	length := c.Len()
	for i := 0; i < length; i++ {
		ins := c.Instruction(i)

		switch v := ins.(type) {
		case instruction.Value:
			dst = append(dst, int(ChangeValue), v.Offset, int(v.X))
		case instruction.Input:
			dst = append(dst, int(InputByte), v.Offset)
		case instruction.Output:
			dst = append(dst, int(OutputByte), v.Offset)
		case instruction.StartLoop:
			dst = append(dst, int(JumpIfZero), v.Offset, 0)
			stack = append(stack, len(dst))
		case instruction.EndLoop:
			if len(stack) == 0 {
				panic("opcode: compile: unexpected Endloop instruction in chunk")
			}
			dst = append(dst, int(JumpIfNotZero), v.Offset, 0)

			start := stack[len(stack)-1]
			stack = stack[:len(stack)-1]

			diff := len(dst) - start
			dst[len(dst)-1], dst[start-1] = diff, diff
		case instruction.Set:
			dst = append(dst, int(SetValue), v.Offset, int(v.X))
		default:
			t := reflect.ValueOf(ins).Elem().Type()
			panic(fmt.Sprintf("opcode: compile: invalid instruction type %s in chunk", t))
		}
	}

	if len(stack) > 0 {
		panic("opcode: compile: unexpected end of chunk, unpaired StartLoop instructions")
	}

	return dst
}
