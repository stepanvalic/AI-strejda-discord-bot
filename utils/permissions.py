import discord
from discord.ext import commands

async def check_permissions(ctx, error):
    """
    Kontroluje, zda uživatel má oprávnění pro příkaz.
    Pokud ne, smaže zprávu a pošle soukromou zprávu.
    """
    # Pokud se nejedná o chybu oprávnění, nic neděláme
    if not isinstance(error, (commands.MissingPermissions, commands.NotOwner)):
        return False
        
    # Smazání zprávy s příkazem
    try:
        await ctx.message.delete()
    except Exception as e:
        print(f"Chyba při mazání zprávy: {str(e)}")
    
    # Poslání soukromé zprávy uživateli
    try:
        embed = discord.Embed(
            title="❌ Nedostatečná oprávnění",
            description=f"Nemáte oprávnění pro použití příkazu `!{ctx.command.name}`.",
            color=discord.Color.red()
        )
        
        if isinstance(error, commands.MissingPermissions):
            missing_perms = ", ".join(error.missing_permissions)
            embed.add_field(
                name="Chybějící oprávnění",
                value=f"Pro tento příkaz potřebujete: **{missing_perms}**"
            )
        elif isinstance(error, commands.NotOwner):
            embed.add_field(
                name="Omezený přístup",
                value="Tento příkaz je dostupný pouze pro vlastníka bota."
            )
            
        await ctx.author.send(embed=embed)
        print(f"Poslána soukromá zpráva uživateli {ctx.author.display_name} o nedostatečných oprávněních")
    except Exception as e:
        print(f"Chyba při posílání soukromé zprávy: {str(e)}")
    
    return True
