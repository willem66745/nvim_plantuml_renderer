# nvim-plantuml-renderer

Personal project for a python based separate Neovim client to render Plantuml,
based on the current buffer content. It is intended to be opened in a separate
console and to connect with a separate Neovim instance.

For example, start Neovim like this:

```sh
nvim --listen localhost:11042
```

And run this tool:

```sh
nvim-plantuml-renderer --port 11042
```

Whenever you edit an Plantuml file or a markdown file in Neovim, show the image or
show why it cannot be rendered. It uses `textual-image` to either render it in console
using Kitty protocol or Sixel protocol.

> [!NOTE]
> I hope this is temporary; Either Neovim gets image support and editor client
> gains support for that. Until then, this helps me. Current solutions either
> doesn't work or requires Kitty protocol based terminals, which does not exits
> in the Windows world (that I must use)
