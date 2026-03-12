import { useEditor, EditorContent, type Editor } from "@tiptap/react"
import StarterKit from "@tiptap/starter-kit"
import Placeholder from "@tiptap/extension-placeholder"
import Link from "@tiptap/extension-link"
import TaskList from "@tiptap/extension-task-list"
import TaskItem from "@tiptap/extension-task-item"
import {
  Bold, Italic, Strikethrough, Code, List, ListOrdered,
  CheckSquare, Link as LinkIcon, Undo, Redo, Quote, Minus,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { Toggle } from "@/components/ui/toggle"

interface RichTextEditorProps {
  content?: string
  onChange?: (html: string) => void
  placeholder?: string
  editable?: boolean
  className?: string
  minimal?: boolean
}

function ToolbarButton({
  action,
  isActive,
  icon: Icon,
  label,
}: {
  editor?: Editor
  action: () => void
  isActive?: boolean
  icon: React.ComponentType<{ className?: string }>
  label: string
}) {
  return (
    <Toggle
      size="sm"
      pressed={isActive}
      onPressedChange={() => action()}
      aria-label={label}
      className="h-7 w-7 p-0"
    >
      <Icon className="h-3.5 w-3.5" />
    </Toggle>
  )
}

function Toolbar({ editor, minimal }: { editor: Editor; minimal?: boolean }) {
  if (minimal) {
    return (
      <div className="flex items-center gap-0.5 border-b px-2 py-1">
        <ToolbarButton editor={editor} action={() => editor.chain().focus().toggleBold().run()} isActive={editor.isActive("bold")} icon={Bold} label="Bold" />
        <ToolbarButton editor={editor} action={() => editor.chain().focus().toggleItalic().run()} isActive={editor.isActive("italic")} icon={Italic} label="Italic" />
        <ToolbarButton editor={editor} action={() => editor.chain().focus().toggleCode().run()} isActive={editor.isActive("code")} icon={Code} label="Code" />
        <ToolbarButton editor={editor} action={() => editor.chain().focus().toggleBulletList().run()} isActive={editor.isActive("bulletList")} icon={List} label="Bullet list" />
        <ToolbarButton editor={editor} action={() => editor.chain().focus().toggleTaskList().run()} isActive={editor.isActive("taskList")} icon={CheckSquare} label="Checklist" />
      </div>
    )
  }

  return (
    <div className="flex items-center gap-0.5 border-b px-2 py-1 flex-wrap">
      <ToolbarButton editor={editor} action={() => editor.chain().focus().toggleBold().run()} isActive={editor.isActive("bold")} icon={Bold} label="Bold" />
      <ToolbarButton editor={editor} action={() => editor.chain().focus().toggleItalic().run()} isActive={editor.isActive("italic")} icon={Italic} label="Italic" />
      <ToolbarButton editor={editor} action={() => editor.chain().focus().toggleStrike().run()} isActive={editor.isActive("strike")} icon={Strikethrough} label="Strikethrough" />
      <ToolbarButton editor={editor} action={() => editor.chain().focus().toggleCode().run()} isActive={editor.isActive("code")} icon={Code} label="Code" />
      <div className="mx-1 h-4 w-px bg-border" />
      <ToolbarButton editor={editor} action={() => editor.chain().focus().toggleBulletList().run()} isActive={editor.isActive("bulletList")} icon={List} label="Bullet list" />
      <ToolbarButton editor={editor} action={() => editor.chain().focus().toggleOrderedList().run()} isActive={editor.isActive("orderedList")} icon={ListOrdered} label="Ordered list" />
      <ToolbarButton editor={editor} action={() => editor.chain().focus().toggleTaskList().run()} isActive={editor.isActive("taskList")} icon={CheckSquare} label="Checklist" />
      <div className="mx-1 h-4 w-px bg-border" />
      <ToolbarButton editor={editor} action={() => editor.chain().focus().toggleBlockquote().run()} isActive={editor.isActive("blockquote")} icon={Quote} label="Blockquote" />
      <ToolbarButton editor={editor} action={() => editor.chain().focus().setHorizontalRule().run()} icon={Minus} label="Divider" />
      <ToolbarButton
        editor={editor}
        action={() => {
          const url = window.prompt("URL")
          if (url) editor.chain().focus().setLink({ href: url }).run()
        }}
        isActive={editor.isActive("link")}
        icon={LinkIcon}
        label="Link"
      />
      <div className="flex-1" />
      <ToolbarButton editor={editor} action={() => editor.chain().focus().undo().run()} icon={Undo} label="Undo" />
      <ToolbarButton editor={editor} action={() => editor.chain().focus().redo().run()} icon={Redo} label="Redo" />
    </div>
  )
}

export function RichTextEditor({
  content = "",
  onChange,
  placeholder = "Write something…",
  editable = true,
  className,
  minimal = false,
}: RichTextEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: { levels: [1, 2, 3] },
      }),
      Placeholder.configure({ placeholder }),
      Link.configure({ openOnClick: false, autolink: true }),
      TaskList,
      TaskItem.configure({ nested: true }),
    ],
    content,
    editable,
    onUpdate: ({ editor }) => {
      onChange?.(editor.getHTML())
    },
    editorProps: {
      attributes: {
        class: cn(
          "prose prose-sm dark:prose-invert max-w-none focus:outline-none",
          "min-h-[80px] px-3 py-2",
          "[&_ul[data-type=taskList]]:list-none [&_ul[data-type=taskList]]:pl-0",
          "[&_ul[data-type=taskList]_li]:flex [&_ul[data-type=taskList]_li]:items-start [&_ul[data-type=taskList]_li]:gap-2",
          "[&_ul[data-type=taskList]_li_label]:mt-0.5",
        ),
      },
    },
  })

  if (!editor) return null

  return (
    <div className={cn("rounded-md border bg-background", className)}>
      {editable && <Toolbar editor={editor} minimal={minimal} />}
      <EditorContent editor={editor} />
    </div>
  )
}

export function RichTextViewer({ content, className }: { content: string; className?: string }) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Link.configure({ openOnClick: true }),
      TaskList,
      TaskItem,
    ],
    content,
    editable: false,
    editorProps: {
      attributes: {
        class: cn(
          "prose prose-sm dark:prose-invert max-w-none",
          "[&_ul[data-type=taskList]]:list-none [&_ul[data-type=taskList]]:pl-0",
          "[&_ul[data-type=taskList]_li]:flex [&_ul[data-type=taskList]_li]:items-start [&_ul[data-type=taskList]_li]:gap-2",
          className,
        ),
      },
    },
  })

  if (!editor) return null
  return <EditorContent editor={editor} />
}
